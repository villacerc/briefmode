# app/services/translation_service.py
from models import TranscriptSnippet, Language, Word, Video, SnippetType
from app.stores import TranslationStore, VideoStore, WordStore, SnippetStore
from .ai_service import AIService
from typing import List, Dict

class TranslationService:
    SEMAPHORE_CONCURRENCY = 10

    def __init__(self, db):
        self.translation_store = TranslationStore(db)
        self.word_store = WordStore(db)
        self.video_store = VideoStore(db)
        self.snippet_store = SnippetStore(db)
        self.ai_service = AIService()

    async def get_ts_snippet_translated_data(self, ts_snippet: TranscriptSnippet, target_lang: Language):
        existing_translation = await self.translation_store.get_snippet_translation_by_lang(ts_snippet.id, target_lang.id)
        if existing_translation:
            return await self.get_normalized_ts_translated_snippet(ts_snippet, target_lang)

        snippet = await self.snippet_store.get_snippet_by_id(ts_snippet.snippet_id)
        parsed_json = await self.ai_service.fetch_ai_snippet_translation(snippet.text, target_lang)

        await self.translation_store.save_ai_ts_snippet_translation(ts_snippet, target_lang, parsed_json)

        return await self.get_normalized_ts_translated_snippet(ts_snippet, target_lang)
    
    async def get_normalized_ts_translated_snippet(self, ts_snippet: TranscriptSnippet, target_lang: Language) -> Dict:
        try:
            video = await self.video_store.get_video_by_id(ts_snippet.video_id, eager_load=True)
            snippet_translation = await self.translation_store.get_snippet_translation_by_lang(ts_snippet.snippet_id, target_lang.id)
            snippet_words = await self.word_store.get_snippet_words(SnippetType.TRANSCRIPT, ts_snippet.id)
            word_translations = [
                await self.translation_store.get_word_translations_by_lang(sw.word_id, target_lang.id)
                for sw in snippet_words
            ]
            
            normalized_snippet_words = [{
                "text": w.text,
                "part_of_speech": w.part_of_speech_tag,
                "romanized": w.word.romanized,
                "translations": [{"text": t.text} for t in word_translations[i]],
                "order_index": w.order_index
            } for i, w in enumerate(snippet_words)]

            return {
                "snippet_id": ts_snippet.id,
                "text": ts_snippet.text,
                "translation": snippet_translation.text,
                "source_lang_code": video.language.code,
                "target_lang_code": target_lang.code,
                "start": ts_snippet.start,
                "end": ts_snippet.end,
                "duration": ts_snippet.duration,
                "snippet_words": normalized_snippet_words
            }
        except Exception as e:
            raise RuntimeError(f"Error normalizing translated snippet. {e}") from e
