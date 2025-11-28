# app/services/translation_service.py
from models import TranscriptSnippet, Language, Word, Translation, Video
from app.stores import TranslationStore, VideoStore
from .ai_service import AIService
from typing import List, Dict

class TranslationService:
    SEMAPHORE_CONCURRENCY = 10

    def __init__(self, db):
        self.translation_store = TranslationStore(db)
        self.video_store = VideoStore(db)
        self.ai_service = AIService()

    async def get_ts_snippet_translated_data(self, ts_snippet: TranscriptSnippet, target_lang: Language):
        existing_translation = await self.translation_store.get_snippet_translation_by_lang(ts_snippet.id, target_lang.id)
        if existing_translation:
            return "success"
            # loaded_translated_ts_snippet = await self.translation_store.get_loaded_translated_ts_snippet(ts_snippet.id, target_lang.id)
            # return self.get_normalized_ts_translated_snippet(loaded_translated_ts_snippet, target_lang)

        # Call AI, parse JSON, etc.
        parsed_json = await self.ai_service.fetch_ai_snippet_translation(ts_snippet.snippet.text, target_lang)

        # Save to DB
        await self.translation_store.save_ai_ts_snippet_translation(ts_snippet, target_lang, parsed_json)

        return "success"
        # loaded_translated_ts_snippet = await self.translation_store.get_loaded_translated_ts_snippet(ts_snippet.id, target_lang.id)
        # return self.get_normalized_ts_translated_snippet(loaded_translated_ts_snippet, target_lang)
    
    def get_normalized_ts_translated_snippet(self, ts_snippet: TranscriptSnippet, target_lang: Language) -> Dict:
        try:
            normalized_snippet_words = [{
                "text": w.text,
                "part_of_speech": w.part_of_speech_tag,
                "romanized": w.word.romanized,
                "translations": [{"text": t.text} for t in w.word.translations],
                "order_index": w.order_index
            } for w in ts_snippet.snippet_words]

            return {
                "snippet_id": ts_snippet.id,
                "text": ts_snippet.text,
                "translation": ts_snippet.snippet.translations[0].text,
                "source_lang_code": ts_snippet.video.language.code,
                "target_lang_code": target_lang.code,
                "start": ts_snippet.start,
                "end": ts_snippet.end,
                "duration": ts_snippet.duration,
                "snippet_words": normalized_snippet_words
            }
        except Exception as e:
            raise RuntimeError(f"Error normalizing translated snippet. {e}") from e
