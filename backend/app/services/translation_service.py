# app/services/translation_service.py
import asyncio
import json
from models import TranscriptSnippet, Language, Word, Translation, Video
from app.stores import TranslationStore, VideoStore
from .helpers import validate_translation_json
from openai import AsyncOpenAI
from typing import List, Dict
import os

class TranslationService:
    SEMAPHORE_CONCURRENCY = 10

    def __init__(self, db):
        self.db = db
        self.store = TranslationStore(db)
        self.video_store = VideoStore(db)
        self.async_openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Assume this is initialized elsewhere

    async def get_translations(self, snippets: List[TranscriptSnippet], lang: Language) -> List[Dict]:
        # Create a semaphore to limit concurrency to avoid overloading API and database
        semaphore = asyncio.Semaphore(self.SEMAPHORE_CONCURRENCY)
    
        async def worker(snippet: TranscriptSnippet, lang: Language):
            async with semaphore:
                translated_snippet = await self.get_translated_snippet(snippet, lang)
                return translated_snippet

        try:
            # Return a list of all translated snippets in same order
            # * unpacks the iterable into individual arguments for a function.
            # eg. (worker(a), worker(b), worker(c))
            return await asyncio.gather(*(worker(s, lang) for s in snippets))
        except Exception as e:
            raise RuntimeError(f"Error occurred while translating snippets. {e}")

    async def get_translated_snippet(self, snippet: TranscriptSnippet, lang: Language):
        if self.snippet_has_translation_for_language(snippet.id, lang.id):
            video = self.video_store.get_video(snippet.video_id)
            return self.get_normalized_translated_snippet(snippet, lang, video)

        # Call AI, parse JSON, etc.
        parsed_json = await self.fetch_ai_translation(snippet, lang)

        # Save to DB
        self.store.save_translation(snippet.id, lang.id, parsed_json)

        video = self.video_store.get_video(snippet.video_id)
        return self.get_normalized_translated_snippet(snippet, lang, video)

    async def retry_with_backoff(self, coro, retries=5, base_delay=1):
        for attempt in range(retries):
            try:
                return await coro
            except Exception as e:
                if attempt == retries - 1:
                    raise RuntimeError(f"Operation failed after {retries} attempts. {str(e)}") from e
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                await asyncio.sleep(delay)

    def snippet_has_translation_for_language(self, snippet_id: int, lang_id: int) -> bool:
        translations = self.store.get_translations_by_snippet_and_language(snippet_id, lang_id)
        return len(translations) > 0

    async def fetch_ai_translation(self, snippet, lang):
        parsed_json = None
        max_retries = 3
        for attempt in range(max_retries):
            # Call the AI model
            response = await self.retry_with_backoff(
                self.async_openai_client.responses.create(
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
                return parsed_json
            except (json.JSONDecodeError, ValueError) as e:
                print(
                    f"Attempt {attempt + 1}/{max_retries} failed: {type(e).__name__} - {e}. Retrying..."
                )
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to parse AI response after {max_retries} attempts. Last error: {e}") from e
                await asyncio.sleep(1)

    def get_normalized_translated_snippet(self, snippet: TranscriptSnippet, lang: Language, video: Video) -> Dict:
        try:
            words = self.db.query(Word).join(Translation).filter(
                Word.transcript_snippet_id == snippet.id,
                Translation.language_id == lang.id
            ).all()

            translation_snippet = self.store.get_translation_snippet_by_language(snippet.id, lang.id)

            snippet_words = [{
                "text": w.text,
                "romanized": w.romanized,
                "translations": [{"text": t.text, "order_index": t.order_index} for t in w.translations],
                "order_index": w.order_index
            } for w in words]

            return {
                "text": snippet.text,
                "translation": translation_snippet.text if translation_snippet else "",
                "transcript_language": video.language.code,
                "translation_language": lang.code,
                "start": snippet.start,
                "end": snippet.end,
                "duration": snippet.duration,
                "snippet_words": snippet_words
            }
        except Exception as e:
            raise RuntimeError(f"Error normalizing translated snippet. {e}") from e
