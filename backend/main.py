from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from youtube_transcript_api import YouTubeTranscriptApi, FetchedTranscriptSnippet
import re
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

executor = ThreadPoolExecutor()

app = FastAPI(
    title="Briefmode",
    description="YouTube Video Blog Posts",
    version="1.0.0"
)

ytt_api = YouTubeTranscriptApi()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
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

@app.get("/video/{video_id}", summary="Get Video Translation")
async def get_video(video_id: str):
    """
    Fetch translation for a specific video ID.
    """
    try:
        transcript = await get_transcript_by_id(video_id)
        transcript = transcript[:15]
        translations = await translate_transcript(transcript)
        translated_snippets = create_translated_snippets(transcript, translations)
        return {
            "message": "Transcript fetched successfully",
            "data": translated_snippets
        }
    except Exception as e:
        print(f"Error occurred while fetching video transcript: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch transcript for video ID {video_id}: {str(e)}"
        )

async def get_transcript_by_id(id: str):
    """
    Internal function to fetch transcript by video ID.
    """
    try:
        transcript = ytt_api.fetch(id)
        return transcript
    except Exception as e:
        raise RuntimeError(f"Failed to fetch transcript for {id}") from e
    
async def translate_transcript(transcript: List[FetchedTranscriptSnippet]) -> List[str]:
    """
    Translate the transcript to desired language.
    """
    input_lines = get_transcript_input_lines(transcript)
    input = f"""
Translate each input line below to Filipino.
{translation_rules.replace("\\n", "\n")}
input:
{input_lines}
    """  
    try:
        response = openai_client.responses.create(
            model="gpt-4.1-nano",
            input=input,
            store=False,
        )
        text = response.output[0].content[0].text
        lines = text.split("\n")

        # remove numbering
        return [re.sub(r'^\s*\d+\.\s*', '', line).strip() for line in lines]
    except Exception as e:
        raise RuntimeError(f"Failed to translate transcript: {str(e)}")

def create_translated_snippets(transcript: List[FetchedTranscriptSnippet], translations: List[str]) -> List[TranslatedSnippet]:
    """
    Create a list of translated snippets from the original transcript and translations.
    """
    snippets: List[TranslatedSnippet] = []

    for i, (t, tr) in enumerate(zip(transcript, translations)):
        start = t.start
        # end is the next snippet's start, or t.start + t.duration for last snippet
        if i < len(transcript) - 1:
            end = transcript[i + 1].start
        else:
            end = t.start + t.duration  # fallback if no next snippet
        snippets.append(
            TranslatedSnippet(
                text=t.text,
                translation=tr,
                start=start,
                end=end,
                duration=t.duration
            )
        )
    return snippets

def chunk_list(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

def get_transcript_input_lines(transcript: List[FetchedTranscriptSnippet]) -> str:
       """
       Prepare the transcript input lines for translation.
       """
       return "\n".join([f"{i + 1}. {snippet.text}" for i, snippet in enumerate(transcript)])
    
def chunk_list(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)