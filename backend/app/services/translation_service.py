# app/services/translation_service.py
from models import TranscriptSnippet, Language, Word, Translation, Video
from app.stores import TranslationStore, VideoStore
from .ai_service import AIService
from typing import List, Dict
import asyncio

class TranslationService:
    SEMAPHORE_CONCURRENCY = 10

    def __init__(self, db):
        self.db = db
        self.translation_store = TranslationStore(db)
        self.video_store = VideoStore(db)
        self.ai_service = AIService()

    async def get_ts_translations(self, ts_snippets: List[TranscriptSnippet], translation_lang: Language) -> List[Dict]:
        # Create a semaphore to limit concurrency to avoid overloading API and database
        semaphore = asyncio.Semaphore(self.SEMAPHORE_CONCURRENCY)

        async def worker(ts_snippet: TranscriptSnippet, translation_lang: Language):
            async with semaphore:
                translated_snippet = await self.get_ts_translated_snippet(ts_snippet, translation_lang)
                return translated_snippet

        try:
            # Return a list of all translated snippets in same order
            # * unpacks the iterable into individual arguments for a function.
            # eg. (worker(a), worker(b), worker(c))
            return await asyncio.gather(*(worker(s, translation_lang) for s in ts_snippets))
        except Exception as e:
            raise RuntimeError(f"Error occurred while translating snippets. {e}")

    async def get_ts_translated_snippet(self, ts_snippet: TranscriptSnippet, translation_lang: Language):
        if self.ts_snippet_has_translation_for_language(ts_snippet.snippet_id, translation_lang.id):
            video = self.video_store.get_video(ts_snippet.video_id)
            return self.get_normalized_ts_translated_snippet(ts_snippet, translation_lang, video)

        # Call AI, parse JSON, etc.
        parsed_json = await self.ai_service.fetch_ai_snippet_translation(ts_snippet.snippet.text, translation_lang)

        # Save to DB
        self.translation_store.save_ai_ts_snippet_translation(ts_snippet, translation_lang, parsed_json)

        video = self.video_store.get_video(ts_snippet.video_id)
        return self.get_normalized_ts_translated_snippet(ts_snippet, translation_lang, video)

    def ts_snippet_has_translation_for_language(self, snippet_id: int, lang_id: int) -> bool:
        translation = self.translation_store.get_snippet_translation_by_language(snippet_id, lang_id)
        return translation is not None

    def get_normalized_ts_translated_snippet(self, ts_snippet: TranscriptSnippet, translation_lang: Language, video: Video) -> Dict:
        try:
            snippet_words = ts_snippet.snippet_words

            snippet_translation = self.translation_store.get_snippet_translation_by_language(ts_snippet.snippet_id, translation_lang.id)

            normalized_snippet_words = [{
                "text": w.text,
                "part_of_speech": w.part_of_speech_tag,
                "romanized": w.word.romanized,
                "translations": [{"text": t.text} for t in w.word.translations],
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
