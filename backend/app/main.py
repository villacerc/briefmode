from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import uvicorn
from concurrent.futures import ThreadPoolExecutor
import os
from dotenv import load_dotenv
import json
from sqlalchemy import select
from sqlalchemy.orm import Session
from models import TranscriptSnippet, Language
from database import get_db
import logging
from app.services import VideoService, TranslationService, DictionaryService
from app.stores import LanguageStore

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

@app.get("/api/dictionary/{input}", summary="Get Input Definition")
async def get_input_definition(input: str):
    db = next(get_db())
    try:
        interpretation = await DictionaryService(db).get_dictionary_entry(input)
        return {"data": interpretation}
    except Exception as e:
        message = f"Error occurred while attempting to fetch input definition for '{input}'. {e}"
        logger.error(message)
        raise HTTPException(
            status_code=500,
            detail=message
        )

@app.get("/api/video/{source_id}", summary="Get Video Translation")
def get_video(source_id: str, lang: str):
    try:
        return StreamingResponse(
            stream_translations(source_id, lang),
            media_type="application/json"
        )
    except Exception as e:
        message = f"Error occurred while attempting to translate video (id: {source_id}). {e}"
        logger.error(message)
        raise HTTPException(
            status_code=500,
            detail=message
        )

@app.get("/api/languages", summary="Get Languages")
def get_video_languages():
    db = next(get_db())
    try:
        languages = db.execute(select(Language)).scalars().all()
        return {"data": languages}
    except Exception as e:
        message = f"Error occurred while attempting to fetch languages. {e}"
        logger.error(message)
        raise HTTPException(
            status_code=500,
            detail=message
        )
    finally:
        db.close()

# Stream translations for the transcript.
async def stream_translations(source_id: str, lang: str):
    db = next(get_db())

    try:
        translation_lang = LanguageStore(db).get_by_code(lang)
        if not translation_lang:
            raise ValueError(f"Language with code '{lang}' not found.")

        transcript_snippets = VideoService(db).fetch_transcript_snippets(source_id)
        transcript_snippets = transcript_snippets[:5]  # Limit to first 5 snippets for testing

        chunk_size = 15
        for i in range(0, len(transcript_snippets), chunk_size):
            transcript_chunk = transcript_snippets[i:i+chunk_size]
            try:
                translated_chunk = await TranslationService(db).get_translations(transcript_chunk, translation_lang)
                yield json.dumps({"message": "Chunk translated", "data": translated_chunk}, ensure_ascii=False) + "\n"
            except Exception as e:
                yield json.dumps({"message": "Failed to translate chunk", "chunk_index": i, "error": str(e)}, ensure_ascii=False) + "\n"
    finally:
        db.close()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)