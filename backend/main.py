from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
from youtube_transcript_api import YouTubeTranscriptApi, FetchedTranscriptSnippet
import re
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI, AsyncOpenAI
import os
from dotenv import load_dotenv
from dataclasses import dataclass, asdict
import random
import json

load_dotenv()

executor = ThreadPoolExecutor()

app = FastAPI(
    title="Briefmode",
    description="YouTube Video Blog Posts",
    version="1.0.0"
)

ytt_api = YouTubeTranscriptApi()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
async_openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
translation_rules = os.getenv("TRANSLATION_RULES", "")

@dataclass
class TranslatedSnippet:
    text: str
    translation: str
    start: float
    end: float
    duration: float

# API Routes
@app.get("/", summary="Health Check")
async def root():
    """Simple health check endpoint."""
    return {
        "message": "YouTube Transcript API is running",
        "status": "healthy",
        "version": "1.0.0"
    }

# Fetch translation for a specific video ID.
@app.get("/video/{video_id}", summary="Get Video Translation")
async def get_video(video_id: str):
    try:
        transcript = await get_transcript_by_id(video_id)
        translations_generator = stream_translations(transcript)
        
        return StreamingResponse(translations_generator, media_type="application/json")
    except Exception as e:
        print(f"Error occurred while attempting to translate video: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error occurred while attempting to translate video (video ID: {video_id}): {str(e)}"
        )

# Internal function to fetch transcript by video ID.
async def get_transcript_by_id(id: str):
    try:
        transcript = ytt_api.fetch(id)
        return transcript
    except Exception as e:
        raise RuntimeError(f"Failed to fetch transcript for {id}") from e

# Create translated snippets from the original transcript and translations. 
def create_translated_snippets(transcript: List[FetchedTranscriptSnippet], translations: List[str]) -> List[dict]:
    snippets: List[dict] = []

    for i, (t, tr) in enumerate(zip(transcript, translations)):
        start = t.start
        # end is the next snippet's start, or t.start + t.duration for last snippet
        if i < len(transcript) - 1:
            end = transcript[i + 1].start
        else:
            end = t.start + t.duration  # fallback if no next snippet
        snippet = TranslatedSnippet(
            text=t.text,
            translation=tr,
            start=start,
            end=end,
            duration=t.duration
        )
        # Convert to dict for JSON serialization
        snippets.append(asdict(snippet))
    return snippets

# Prepare the transcript input lines for translation.
def get_transcript_input_lines(transcript: List[FetchedTranscriptSnippet]) -> str:
       return "\n".join([f"{i + 1}. {snippet.text}" for i, snippet in enumerate(transcript)])

# Stream translations for the transcript.
async def stream_translations(transcript: List[FetchedTranscriptSnippet]):
    # Break transcript into chunks
    chunk_size = 15 
    for i in range(0, len(transcript), chunk_size):
        transcript_chunk = transcript[i:i + chunk_size]

        try:
            translation_chunk = await translate_transcript(transcript_chunk)
            translated_snippets = create_translated_snippets(transcript_chunk, translation_chunk)

            # Send it to the client immediately
            yield json.dumps({
                "message": "Chunk translated",
                "data": translated_snippets
            }) + "\n"
        except Exception as e:
            yield json.dumps({
                "message": "Failed to translate chunk",
                "chunk_index": i,
                "error": str(e)
            }) + "\n"

# Retry a coroutine with exponential backoff.
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

async def translate_snippet(snippet):
    try:
        response = await retry_with_backoff(
            async_openai_client.responses.create(
                model="gpt-4.1-nano",
                input=f"""
                Translate the input below to Filipino.
                Rules:
                - Do not add explanations.
                - Do not add ellipsis.
                - Respond with only the translation.
                input:
                {snippet}""",
                store=False,
            )
        )
        return response.output[0].content[0].text
    except Exception as e:
        raise RuntimeError(f"Failed to translate snippet: {str(e)}")

async def translate_transcript(snippets, concurrency=10):
    semaphore = asyncio.Semaphore(concurrency)

    async def worker(snippet):
        async with semaphore:
            return await translate_snippet(snippet)
    
    return await asyncio.gather(*(worker(s) for s in snippets))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)