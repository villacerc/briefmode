# app/services/translation_service.py
import asyncio
import json
from models import TranscriptSnippet, Language, Word, Translation, Video, SnippetWord
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

    async def get_translations(self, ts_snippets: List[TranscriptSnippet], translation_lang: Language) -> List[Dict]:
        # Create a semaphore to limit concurrency to avoid overloading API and database
        semaphore = asyncio.Semaphore(self.SEMAPHORE_CONCURRENCY)

        async def worker(ts_snippet: TranscriptSnippet, translation_lang: Language):
            async with semaphore:
                translated_snippet = await self.get_translated_snippet(ts_snippet, translation_lang)
                return translated_snippet

        try:
            # Return a list of all translated snippets in same order
            # * unpacks the iterable into individual arguments for a function.
            # eg. (worker(a), worker(b), worker(c))
            return await asyncio.gather(*(worker(s, translation_lang) for s in ts_snippets))
        except Exception as e:
            raise RuntimeError(f"Error occurred while translating snippets. {e}")

    async def get_translated_snippet(self, ts_snippet: TranscriptSnippet, translation_lang: Language):
        if self.ts_snippet_has_translation_for_language(ts_snippet.snippet_id, translation_lang.id):
            video = self.video_store.get_video(ts_snippet.video_id)
            return self.get_normalized_translated_snippet(ts_snippet, translation_lang, video)

        # Call AI, parse JSON, etc.
        parsed_json = await self.fetch_ai_translation(ts_snippet.snippet.text, translation_lang)

        # Save to DB
        self.store.save_translation(ts_snippet, translation_lang.id, parsed_json)

        video = self.video_store.get_video(ts_snippet.video_id)
        return self.get_normalized_translated_snippet(ts_snippet, translation_lang, video)

    async def retry_with_backoff(self, coro, retries=5, base_delay=1):
        for attempt in range(retries):
            try:
                return await coro
            except Exception as e:
                if attempt == retries - 1:
                    raise RuntimeError(f"Operation failed after {retries} attempts. {str(e)}") from e
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                await asyncio.sleep(delay)

    def ts_snippet_has_translation_for_language(self, snippet_id: int, lang_id: int) -> bool:
        translation = self.store.get_snippet_translation_by_language(snippet_id, lang_id)
        return translation is not None

    async def fetch_ai_translation(self, snippet_text, translation_lang):
        parsed_json = None
        max_retries = 3
        for attempt in range(max_retries):
            # Call the AI model
            response = await self.retry_with_backoff(
                self.async_openai_client.responses.create(
                    model="gpt-4.1-nano",
                    input=f"""
                    Translate the input below to {translation_lang.name}.
                    Rules:
                    1. Respond ONLY with valid JSON. Do NOT include explanations, comments, or extra text.
                    2. Capitalize the first word only if required by grammar.
                    3. Break down input into individual words or tokens, including:
                       - "word": original word
                       - "part_of_speech": only include the **main POS label** (e.g., "verb"), not long explanations.
                       - "romanized": Latin script romanization, "" if already Latin
                       - "translations": at least three translation candidates if possible.
                    4. "romanized" must never contain non-Latin characters.
                    5. Use properly formatted JSON, double quotes, no trailing commas.

                    Output JSON format:

                    {{
                      "translation": "<full translated sentence here>",
                      "word_parts": [
                        {{
                          "word": "<original word>",
                          "part_of_speech": "<part of speech>",
                          "romanized": "<romanized form in Latin or ''>",
                          "translations": [{{ "translation": "<translated word>" }}]
                        }}
                      ]
                    }}

                    Input:
                    {snippet_text}
                    """,
                    store=False
                )
            )

            raw_text = response.output[0].content[0].text.strip()
            try:
                parsed_json = json.loads(raw_text)
                validate_translation_json(parsed_json, snippet_text)
                return parsed_json
            except (json.JSONDecodeError, ValueError) as e:
                print(
                    f"Attempt {attempt + 1}/{max_retries} failed: {type(e).__name__} - {e}. Retrying..."
                )
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to parse AI response after {max_retries} attempts. Last error: {e}") from e
                await asyncio.sleep(1)

    def get_normalized_translated_snippet(self, ts_snippet: TranscriptSnippet, translation_lang: Language, video: Video) -> Dict:
        try:
            snippet_words = ts_snippet.snippet.snippet_words

            snippet_translation = self.store.get_snippet_translation_by_language(ts_snippet.snippet_id, translation_lang.id)

            normalized_snippet_words = [{
                "text": w.text,
                "part_of_speech": w.part_of_speech,
                "romanized": w.word.romanized,
                "translations": [{"text": t.text, "order_index": t.order_index} for t in w.word.translations],
                "order_index": w.order_index
            } for w in snippet_words]

            return {
                "snippet_id": ts_snippet.id,
                "text": ts_snippet.text,
                "translation": snippet_translation.text if snippet_translation else "",
                "transcript_language": ts_snippet.snippet.language.code,
                "translation_language": translation_lang.code,
                "start": ts_snippet.start,
                "end": ts_snippet.end,
                "duration": ts_snippet.duration,
                "snippet_words": normalized_snippet_words
            }
        except Exception as e:
            raise RuntimeError(f"Error normalizing translated snippet. {e}") from e
