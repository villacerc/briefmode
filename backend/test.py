from urllib import response
from youtube_transcript_api import YouTubeTranscriptApi
import asyncio
from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
import json
from dataclasses import dataclass, field
from openai import OpenAI, AsyncOpenAI
import random
import time

load_dotenv()

@dataclass
class TranscriptSnippet:
    text: str
    translation: str
    start: float
    duration: float

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)
async_openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

# input_list = [
#     "This is me at 19 years old. I was broke,",
#     "struggling in school, but with a dream",
#     "that one day I'll make it big. Today, I",
#     "can travel wherever I want to, dine at",
#     "the finest restaurants, and have the",
#     "freedom to do the things that I'm",
#     "passionate about. This is the story of",
#     "how I went from broke to becoming a",
#     "millionaire in 24 months. It was the",
#     "first quarter of 2019, the second year",
#     "of my school. I was studying information",
#     "technology and struggled with most of my",
#     "modules. Because of my low GPA and lack",
#     "of interest in studying, I knew that I",
#     "couldn't make it to university. That's",
#     "a change or remain unsuccessful for the",
#     "rest of my life. Given my interest in",
#     "entrepreneurship since young, my goal",
#     "has always been to start a business, one",
#     "that can make me wealthy and break free",
#     "from the traditional 9 to5 path. During",
#     "a bus ride home from school, I thought",
#     "of an idea that I hoped would",
#     "revolutionize social media marketing"
# ]

prompt = f"""
Translate each input line below to Filipino.  
 Rules:  
- Output must have the exact same number of lines as the input.
- There are no empty output lines.
- Do not merge lines.  
- Do not add explanations. Only translations.  
"""

def chunk_list(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

async def main():

    ytt_api = YouTubeTranscriptApi()
    
    transcript_list = ytt_api.list("2wlMlDON1rg")
    first_transcript = next(iter(transcript_list))  # <-- use iter() + next()
    transcript = ytt_api.fetch("2wlMlDON1rg", languages=[first_transcript.language_code])
    print(transcript)
    # for t in transcripts:
    #     print(t.language_code, t.language, t.is_generated)
    # input_list = [snippet.text for snippet in transcript.snippets]
    # print(input_list)

    # translate_chunk(input_list[:15])
    # batch_translations(input_list)
    # translations = await translate_transcript(input_list, concurrency=20)
    # for i,t in enumerate(translations):
    #     print(f"{i + 1}. {t}")

def batch_translations(input_list):
    # input_lines = "\n".join([snippet.text for snippet in input_list])
    input_lines = input_list
    jobs = [
        {
            "custom_id": f"line-{i}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",  # or gpt-3.5-turbo / any supported model
                "messages": [
                    {"role": "system", "content": "You are a helpful translator."},
                    {"role": "user", "content": f"Translate to Filipino: {line}"}
                ],
                "max_tokens": 1000
            }
        }
        for i, line in enumerate(input_lines)
    ]
    # Write to .jsonl file  
    with open("batch_input.jsonl", "w", encoding="utf-8") as f:
        for job in jobs:
            f.write(json.dumps(job) + "\n")


def translate_chunk(input_list):
    chunks = list(chunk_list(input_list, 15))

    # for i, chunk in enumerate(chunks):
    #     numbered_chunk = [
    #         f"{j + 1}. {line}" for j, line in enumerate(chunk)
    #     ]
    #     print(f"--- chunk {i+1} ---")
    #     print("\n".join(numbered_chunk))

    # loop over each chunk and send a request
    for i, chunk in enumerate(chunks):
        numbered_chunk = [
            f"{j + 1}. {line}" for j, line in enumerate(chunk)
        ]
        input_lines = "\n".join(numbered_chunk)
        input = f"""
{prompt}
input:
{input_lines}
        """
        response = client.responses.create(
            model="gpt-5-nano",
            input=input,
            store=False,
        )
        
        print(f"--- Translation for chunk {i+1} ---")
        # print(input)
        print(response.output[1].content[0].text) # gpt-5
        # print(response.output[0].content[0].text)

# Simulate exponential backoff for robustness
async def retry_with_backoff(coro, retries=5, base_delay=1):
    for attempt in range(retries):
        try:
            return await coro
        except Exception as e:
            if attempt == retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            print(f"Retrying in {delay:.1f}s after error: {e}")
            await asyncio.sleep(delay)

# Translate one snippet
async def translate_snippet(snippet):
    response = await retry_with_backoff(
        async_openai_client.responses.create(
            model="gpt-4.1-nano",
            input=f"""
            Translate the input below to Filipino.
            Rules:
            - Do not add explanations.
            - Do not add ellipsis.
            - Respond with only the translaation.
            input:
            {snippet}""",
            store=False,
        )
    )
    return response.output[0].content[0].text

async def translate_transcript(snippets, concurrency=10):
    semaphore = asyncio.Semaphore(concurrency)

    async def worker(snippet):
        async with semaphore:
            return await translate_snippet(snippet)

    return await asyncio.gather(*(worker(s) for s in snippets))

if __name__ == "__main__":
    # main()
    asyncio.run(main())