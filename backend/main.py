from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List, Optional, Dict, Any
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI, AsyncOpenAI
import os
from dotenv import load_dotenv
from dataclasses import dataclass, asdict
import random
import json
from sqlalchemy import select
from sqlalchemy.orm import joinedload, Session
from sqlalchemy.exc import SQLAlchemyError
from models import TranscriptSnippet, Video, Language, Translation
from database import get_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

executor = ThreadPoolExecutor()

app = FastAPI(
    title="Briefmode",
    description="YouTube Video Blog Posts",
    version="1.0.0"
)

# TODO: refactor for other environments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

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
@app.get("/api/video/{source_id}", summary="Get Video Translation")
def get_video(source_id: str, to_lang: str):
    try:
        translation_lang = get_language_by_code(to_lang)
        if not translation_lang:
            raise ValueError(f"Language with code '{to_lang}' not found.")

        transcript = get_transcript(source_id)
        translations_generator = stream_translations(transcript, translation_lang)

        return StreamingResponse(translations_generator, media_type="application/json")
    except Exception as e:
        message = f"Error occurred while attempting to translate video (id: {source_id}). {e}"
        logger.error(message)
        raise HTTPException(
            status_code=500,
            detail=message
        )

def get_language_by_code(code: str) -> Language:
    db = next(get_db())
    try:
        language = db.execute(
            select(Language).where(Language.code == code)
        ).scalars().first()

        return language

    except Exception as e:
        raise RuntimeError(f"Failed to fetch language with code '{code}'. {str(e)}") from e
    finally:
        db.close()

def get_transcript(source_id: str) -> List[TranscriptSnippet]:
    db = next(get_db())
    try:
        # Fetch the video
        video = db.execute(
            select(Video).options(joinedload(Video.transcript_snippets))
            .where(Video.source_id == source_id)
        ).scalars().first()

        # Check if transcript already exists
        if video and video.transcript_snippets:
            return video.transcript_snippets

        # Fetch from API
        transcript_data = ytt_api.fetch(source_id)

        # Ensure language exists
        language = get_language_by_code(transcript_data.language_code)

        if not language:
            language = Language(code=transcript_data.language_code, name=transcript_data.language)
            db.add(language)
            db.commit()
            db.refresh(language)

        video = Video(source_id=source_id, language_id=language.id)
        db.add(video)
        db.commit()
        db.refresh(video)

        # Save all snippets at once
        transcript = []
        for i, item in enumerate(transcript_data.snippets):
            snippet = TranscriptSnippet(
                video_id=video.id,
                text=item.text,
                start=item.start,
                end=transcript_data[i + 1].start if i < len(transcript_data) - 1 else item.start + item.duration,
                duration=item.duration
            )
            db.add(snippet)
            transcript.append(snippet)

        db.commit()
        return transcript
    except SQLAlchemyError as e:
        db.rollback()
        raise RuntimeError(f"Database error. {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to fetch transcript. {str(e)}") from e
    finally:
        db.close()

# Stream translations for the transcript.
async def stream_translations(transcript: List[TranscriptSnippet], to_lang: Language):
    # Break transcript into chunks
    chunk_size = 15 
    for i in range(0, len(transcript), chunk_size):
        transcript_chunk = transcript[i:i + chunk_size]

        try:
            translated_chunk = await get_translations(transcript_chunk, to_lang)

            # Send a chunk to the client immediately
            # yield: instead of returning just once, it can produce a series of results over time, pausing between each one.
            yield json.dumps({
                "message": "Chunk translated",
                "data": translated_chunk
            }) + "\n"
        except Exception as e:
            yield json.dumps({
                "message": "Failed to translate chunk",
                "chunk_index": i,
                "error": str(e)
            }) + "\n"

# Retry a coroutine with exponential backoff
# coro is a coroutine AKA async function
async def retry_with_backoff(coro, retries=5, base_delay=1):
    for attempt in range(retries):
        try:
            return await coro
        except Exception as e:
            if attempt == retries - 1:
                raise RuntimeError(f"Operation failed after {retries} attempts. {str(e)}") from e
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            print(f"Retrying in {delay:.1f}s after error: {e}")
            await asyncio.sleep(delay)

async def get_translation(snippet: TranscriptSnippet, to_lang: Language, db: Session):
    try:
        translation = db.query(Translation).filter(
            Translation.snippet_id == snippet.id,
            Translation.language_id == to_lang.id
        ).first()

        if translation:
            return translation
    
        response = await retry_with_backoff(
            async_openai_client.responses.create(
                model="gpt-4.1-nano",
                input=f"""
                Translate the input below to {to_lang.name}.
                Rules:
                - Do not add explanations or ellipsis.
                - Capitalize the first word **only if it is required by grammar**.
                - Respond with only the translation.
                input:
                {snippet.text}""",
                store=False,
            )
        )

        translation = Translation(
            snippet_id=snippet.id,
            language_id=to_lang.id,
            text=response.output[0].content[0].text
        )
        db.add(translation)
        db.commit()

        return translation
    except Exception as e:
        logger.error(f"Failed to translate snippet (id: {snippet.id}). {str(e)}")
        return Translation(
            snippet_id=snippet.id,
            language_id=to_lang.id,
            text="< >"
        )

async def get_translations(snippets: List[TranscriptSnippet], to_lang: Language, concurrency=10) -> List[TranslatedSnippet]:
    # Create a semaphore to limit concurrency to avoid overloading API and database
    semaphore = asyncio.Semaphore(concurrency)

    async def worker(snippet, db):
        async with semaphore:
            translation = await get_translation(snippet, to_lang, db)
            return asdict(TranslatedSnippet(
                text=snippet.text,
                translation=translation.text,
                start=snippet.start,
                end=snippet.end,
                duration=snippet.duration
            ))

    try:
        db = next(get_db())
        # Return a list of all translated snippets in same order
        # * unpacks the iterable into individual arguments for a function.
        # eg. (worker(a), worker(b), worker(c))
        return await asyncio.gather(*(worker(s, db) for s in snippets))
    except Exception as e:
        raise RuntimeError(f"Error occurred while translating snippets. {e}")
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)