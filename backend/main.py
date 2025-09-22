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
from models import TranscriptSnippet, Video, Language, Translation, Word, TranslationSnippet
from database import get_db
import logging
from helpers import validate_translation_json

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
class WordTranslation:
    text: str
    order_index: int

@dataclass
class SnippetWord:
    text: str
    romanized: str
    order_index: int
    translations: List[WordTranslation]

@dataclass
class TranslatedSnippet:
    text: str
    translation: float
    transcript_language: str
    translation_language: str
    start: float
    end: float
    duration: float
    snippet_words: List[SnippetWord]

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
def get_video(source_id: str, lang: str):
    try:
        translation_lang = get_language_by_code(lang)
        if not translation_lang:
            raise ValueError(f"Language with code '{lang}' not found.")

        transcript = get_transcript(source_id)
        translations_generator = stream_translations(transcript[:15], translation_lang)

        return StreamingResponse(translations_generator, media_type="application/json")
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
        transcript_list = ytt_api.list(source_id)
        first_transcript = next(iter(transcript_list))
        transcript_data = ytt_api.fetch(source_id, languages=[first_transcript.language_code])

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
async def stream_translations(transcript: List[TranscriptSnippet], lang: Language):
    # Break transcript into chunks
    chunk_size = 15 
    for i in range(0, len(transcript), chunk_size):
        transcript_chunk = transcript[i:i + chunk_size]

        try:
            translated_chunk = await get_translations(transcript_chunk, lang)

            # Send a chunk to the client immediately
            # yield: instead of returning just once, it can produce a series of results over time, pausing between each one.
            yield json.dumps({
                "message": "Chunk translated",
                "data": translated_chunk
            }, ensure_ascii=False) + "\n"
        except Exception as e:
            yield json.dumps({
                "message": "Failed to translate chunk",
                "chunk_index": i,
                "error": str(e)
            }, ensure_ascii=False) + "\n"

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
            await asyncio.sleep(delay)

from sqlalchemy.orm import contains_eager

async def get_normalized_translated_snippet(snippet: TranscriptSnippet, lang: Language, db: Session):
    try:
        words = db.query(Word).join(Translation).filter(
            Word.transcript_snippet_id == snippet.id,
            Translation.language_id == lang.id
        ).options(contains_eager(Word.translations)).all()

        translation_snippet = db.query(TranslationSnippet).filter(
            TranslationSnippet.transcript_snippet_id == snippet.id,
            TranslationSnippet.language_id == lang.id
        ).first()

        video = db.query(Video).filter(Video.id == snippet.video_id).first()

        snippet_words: List[SnippetWord] = []

        for word in words:
            translations: List[WordTranslation] = [
                WordTranslation(
                    text=t.text,
                    order_index=t.order_index
                )
                for t in word.translations
            ]
            snippet_word = SnippetWord(
                text=word.text,
                romanized=word.romanized,
                translations=translations,
                order_index=word.order_index
            )
            snippet_words.append(snippet_word)

        return asdict(TranslatedSnippet(
            text=snippet.text,
            translation=translation_snippet.text,
            transcript_language=video.language.code,
            translation_language=lang.code,
            start=snippet.start,
            end=snippet.end,
            duration=snippet.duration,
            snippet_words=snippet_words
        ))
    except Exception as e:
        raise RuntimeError(f"Failed to normalize translated snippet. {str(e)}") from e


async def get_translated_snippet(snippet: TranscriptSnippet, lang: Language, db: Session):
    try:
        # Check if translation already exists
        has_translation = db.query(Translation).join(Word).filter(
            Word.transcript_snippet_id == snippet.id,
            Translation.language_id == lang.id
        ).first() is not None

        if has_translation:
            return await get_normalized_translated_snippet(snippet, lang, db)

        parsed_json = None
        max_retries = 3
        for attempt in range(max_retries):
            # Call the AI model
            response = await retry_with_backoff(
                async_openai_client.responses.create(
                    model="gpt-4.1-nano",
                    input=f"""
                    Translate the input below to {lang.name}.
                    Rules:
                    1. Respond ONLY with valid JSON. Do NOT include explanations, comments, or extra text.
                    2. Capitalize the first word only if required by grammar.
                    3. Break down input into individual words or tokens, including:
                       - "word": original word
                       - "romanized": Latin script romanization, "" if already Latin
                       - "translations": main translation first, up to 2 alternatives
                    4. "romanized" must never contain non-Latin characters.
                    5. Use properly formatted JSON, double quotes, no trailing commas.

                    Output JSON format:

                    {{
                      "translation": "<full translated sentence here>",
                      "word_parts": [
                        {{
                          "word": "<original word>",
                          "romanized": "<romanized form in Latin or ''>",
                          "translations": [{{ "translation": "<translated word>" }}]
                        }}
                      ]
                    }}

                    Input:
                    {snippet.text}
                    """,
                    store=False
                )
            )

            raw_text = response.output[0].content[0].text.strip()
            try:
                parsed_json = json.loads(raw_text)
                validate_translation_json(parsed_json, snippet.text)
                break  # Successfully parsed, exit retry loop
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {type(e).__name__} - {e}. Retrying..."
                )
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)

        # Save parsed data to the database
        transcript_snippet = TranslationSnippet(
            text=parsed_json.get("translation", ""),
            transcript_snippet_id=snippet.id,
            language_id=lang.id,
        )
        db.add(transcript_snippet)

        for i, part in enumerate(parsed_json.get("word_parts", [])):
            word_part = Word(
                text=part["word"],
                romanized=part["romanized"],
                transcript_snippet_id=snippet.id,
                order_index=i
            )
            db.add(word_part)
            db.commit()
            db.refresh(word_part)
            for j, tpart in enumerate(part.get("translations", [])):
                word_translation = Translation(
                    text=tpart["translation"],
                    word_id=word_part.id,
                    language_id=lang.id,
                    order_index=j
                )
                db.add(word_translation)
        db.commit()

        return await get_normalized_translated_snippet(snippet, lang, db)

    except Exception as e:
        logger.error(f"Failed to translate snippet (id: {snippet.id}). {str(e)}")
        return {}

async def get_translations(snippets: List[TranscriptSnippet], lang: Language, concurrency=10) -> List[TranslatedSnippet]:
    # Create a semaphore to limit concurrency to avoid overloading API and database
    semaphore = asyncio.Semaphore(concurrency)

    async def worker(snippet, db):
        async with semaphore:
            translated_snippet = await get_translated_snippet(snippet, lang, db)
            return translated_snippet

    try:
        # Return a list of all translated snippets in same order
        # * unpacks the iterable into individual arguments for a function.
        # eg. (worker(a), worker(b), worker(c))
        db = next(get_db())
        return await asyncio.gather(*(worker(s, db) for s in snippets))
    except Exception as e:
        raise RuntimeError(f"Error occurred while translating snippets. {e}")
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)