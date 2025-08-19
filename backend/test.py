from urllib import response
from youtube_transcript_api import YouTubeTranscriptApi
import asyncio
from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
import json
from dataclasses import dataclass, field
from openai import OpenAI

@dataclass
class TranscriptSnippet:
    text: str
    translation: str
    start: float
    duration: float

input_list = [
    "This is me at 19 years old. I was broke,",
    "struggling in school, but with a dream",
    "that one day I'll make it big. Today, I",
    "can travel wherever I want to, dine at",
    "the finest restaurants, and have the",
    "freedom to do the things that I'm",
    "passionate about. This is the story of",
    "how I went from broke to becoming a",
    "millionaire in 24 months. It was the",
    "first quarter of 2019, the second year",
    "of my school. I was studying information",
    "technology and struggled with most of my",
    "modules. Because of my low GPA and lack",
    "of interest in studying, I knew that I",
    "couldn't make it to university. That's",
    "a change or remain unsuccessful for the",
    "rest of my life. Given my interest in",
    "entrepreneurship since young, my goal",
    "has always been to start a business, one",
    "that can make me wealthy and break free",
    "from the traditional 9 to5 path. During",
    "a bus ride home from school, I thought",
    "of an idea that I hoped would",
    "revolutionize social media marketing"
]

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

def main():
    
    load_dotenv()
    # ytt_api = YouTubeTranscriptApi()
    # transcript = ytt_api.fetch("oLIkRpKLH1Y")
    # input_lines = "\n".join([snippet.text for snippet in transcript.snippets])
    # print(input_lines)

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
    )
 
    chunks = list(chunk_list(input_list, 15))

    # for i, chunk in enumerate(chunks):
    #     input_lines = "\n".join(chunk)
    #     print(f"--- chunk {i+1} ---")
    #     print(input_lines)

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
            model="gpt-4.1-nano",
            input=input,
            store=False,
        )
        
        print(f"--- Translation for chunk {i+1} ---")
        # print(input)
        # print(response.output_text)
        print(response.output[0].content[0].text)

if __name__ == "__main__":
    main()