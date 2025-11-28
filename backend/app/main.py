from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
import uvicorn
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import json
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import TranscriptSnippet, Language
from database import AsyncSessionLocal
import logging
from app.services import VideoService, TranslationService, DictionaryService, TTSService
from app.stores import LanguageStore, VideoStore
import asyncio

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

# API Routes
@app.get("/", summary="Health Check")
async def root():
    """Simple health check endpoint."""
    return {
        "message": "YouTube Transcript API is running",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/api/tts/{text}", summary="Text to Speech")
async def text_to_speech(text: str, source_lang_code: str):
    db = next(get_db())
    try:
        source_lang = LanguageStore(db).get_lang_by_code(source_lang_code)
        audioBase64 = await TTSService(db).get_tts_audio(text, source_lang)
        return {"audio": audioBase64}
    except Exception as e:
        message = f"Error occurred while attempting to convert text to speech. {e}"
        logger.error(message)
        raise HTTPException(
            status_code=500,
            detail=message
        )

@app.get("/api/dictionary/{text}", summary="Get Input Definition")
async def get_input_definition(text: str, source_lang_code: str, target_lang_code: str):
    db = next(get_db())
    try:
        source_lang = LanguageStore(db).get_lang_by_code(source_lang_code)
        target_lang = LanguageStore(db).get_lang_by_code(target_lang_code)
        dictionary_entry = await DictionaryService(db).get_dictionary_entry(text, source_lang, target_lang)
        return dictionary_entry
    except Exception as e:
        message = f"Error occurred while attempting to fetch input definition for '{text}'. {e}"
        logger.error(message)
        raise HTTPException(
            status_code=500,
            detail=message
        )
    finally:
        db.close()

@app.get("/api/video/{source_id}", summary="Get Video")
async def get_video(source_id: str):
    async with AsyncSessionLocal() as db:
        try:
            video_info = await VideoService(db).fetch_video_info(source_id)
            return video_info
        except Exception as e:
            message = f"Error occurred while attempting to fetch video info (id: {source_id}). {e}"
            logger.error(message)
            raise HTTPException(
                status_code=500,
                detail=message
            )

@app.get("/api/transcript/{video_source_id}", summary="Get Video Transcript and Translations")
async def get_transcript(video_source_id: str, target_lang_code: str):
    try:
        async with AsyncSessionLocal() as db:
            video = await VideoStore(db).get_video_by_source_id(video_source_id)
            if not video:
                raise RuntimeError(f"Video not found (id: {video_source_id})")

        return StreamingResponse(
            stream_translations(video.source_id, target_lang_code),
            media_type="application/json"
        )
    except Exception as e:
        message = f"Error occurred while attempting to translate video (id: {video_source_id}). {e}"
        logger.error(message)
        raise HTTPException(
            status_code=500,
            detail=message
        )

@app.get("/api/languages", summary="Get Languages")
async def get_video_languages():
     async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Language))
            languages = result.scalars().all()
            return {"data": languages}
        except Exception as e:
            message = f"Error occurred while attempting to fetch languages. {e}"
            logger.error(message)
            raise HTTPException(status_code=500, detail=message)

# Stream translations for the transcript.
async def stream_translations(source_id: str, target_lang_code: str):
    try:
        async with AsyncSessionLocal() as db:
            target_lang = await LanguageStore(db).get_lang_by_code(target_lang_code)
            transcript_snippets = await VideoService(db).fetch_transcript_snippets(source_id)
            transcript_snippets = transcript_snippets[:2]  # Limit to first 2 snippets for testing

        chunk_size = 15
        for i in range(0, len(transcript_snippets), chunk_size):
            transcript_chunk = transcript_snippets[i:i+chunk_size]
            try:
                translated_chunk = await translate_chunk(transcript_chunk, target_lang)
                yield json.dumps({"message": "Chunk translated", "data": translated_chunk}, ensure_ascii=False) + "\n"
            except Exception as e:
                yield json.dumps({"message": "Failed to translate chunk", "chunk_index": i, "error": str(e)}, ensure_ascii=False) + "\n"
    except Exception as e:
        raise RuntimeError(f"Error streaming translations for video (id: {source_id}). {e}")

async def translate_chunk(ts_snippets: List[TranscriptSnippet], target_lang: Language) -> List[Dict]:
    # Limit concurrency to avoid overloading API or DB
    semaphore = asyncio.Semaphore(10)

    async def worker(ts_snippet: TranscriptSnippet):
        async with semaphore:
            async with AsyncSessionLocal() as db:
                translated_snippet = await TranslationService(db).get_ts_snippet_translated_data(
                    ts_snippet, target_lang
                )
                return translated_snippet

    try:
        # Run all workers concurrently, safely with separate sessions
        return await asyncio.gather(*(worker(s) for s in ts_snippets))
    except Exception as e:
        raise RuntimeError(f"Error occurred while translating snippets: {e}")
        
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)