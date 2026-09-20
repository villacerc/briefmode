from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
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

@app.get("/api/word_tts/{word_id}", summary="Text to Speech")
async def text_to_speech(word_id: int):
    async with AsyncSessionLocal() as db:
        try:
            audioBase64 = await TTSService(db).get_word_tts_audio(word_id)
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
    async with AsyncSessionLocal() as db:
        try:
            source_lang = await LanguageStore(db).get_lang_by_code(source_lang_code)
            target_lang = await LanguageStore(db).get_lang_by_code(target_lang_code)
            dictionary_entry = await DictionaryService(db).get_dictionary_entry(text, source_lang, target_lang)
            return dictionary_entry
        except Exception as e:
            message = f"Error occurred while attempting to fetch input definition for '{text}'. {e}"
            logger.error(message)
            raise HTTPException(
                status_code=500,
                detail=message
            )

@app.get("/api/video/{source_id}", summary="Get Video")
async def get_video(source_id: str):
    async with AsyncSessionLocal() as db:
        try:
            video_data = await VideoService(db).get_video_data(source_id)
            return video_data
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
                video = await VideoService(db).fetch_video(video_source_id)
            
            video_transcript_snippets = await VideoService(db).fetch_transcript_snippets(video)
            video_transcript_snippets = video_transcript_snippets[:3]
            
        return StreamingResponse(
            stream_translations(video_transcript_snippets, target_lang_code),
            media_type="application/x-ndjson",
            headers={"X-Accel-Buffering": "no"}
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
async def stream_translations(ts_snippets: list[TranscriptSnippet], target_lang_code: str):
    try:
        async with AsyncSessionLocal() as db:
            source_lang = await LanguageStore(db).get_lang_by_id(ts_snippets[0].video.language_id)
            target_lang = await LanguageStore(db).get_lang_by_code(target_lang_code)

        chunk_size = 1
        for i in range(0, len(ts_snippets), chunk_size):
            transcript_chunk = ts_snippets[i:i+chunk_size]
            try:
                translated_chunk = await translate_chunk(transcript_chunk, source_lang, target_lang)
                yield json.dumps({"type": "chunk", "status": "success", "index": i, "data": translated_chunk}, ensure_ascii=False) + "\n"
            except Exception as e:
                yield json.dumps({"type": "chunk", "status": "error", "index": i, "error": str(e)}, ensure_ascii=False) + "\n"
        yield json.dumps({"type": "complete"}, ensure_ascii=False) + "\n"
    except Exception as e:
        raise RuntimeError(f"Error streaming translations. {e}")

async def translate_chunk(ts_snippets: list[TranscriptSnippet], source_lang: Language, target_lang: Language) -> list[Dict]:
    async with AsyncSessionLocal() as db:
        try:
            return await TranslationService(db).get_ts_snippets_translated_data(ts_snippets, source_lang, target_lang)
        except Exception as e:
            raise RuntimeError(f"Error occurred while translating snippets: {e}")
        
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)