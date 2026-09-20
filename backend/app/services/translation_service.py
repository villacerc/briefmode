# app/services/translation_service.py
from models import TranscriptSnippet, Language, AIPromptType, SnippetTranslation, Snippet
from app.stores import VideoStore, WordStore, SnippetStore, WordTranslationStore, SnippetTranslationStore, SnippetWordStore
from .ai_service import AIService
from typing import List, Dict
from collections import defaultdict
import asyncio
from app.utils.helpers import sanitize_word

class TranslationService:
    def __init__(self, db):
        self.word_store = WordStore(db)
        self.snippet_word_store = SnippetWordStore(db)
        self.video_store = VideoStore(db)
        self.word_translation_store = WordTranslationStore(db)
        self.snippet_translation_store = SnippetTranslationStore(db)
        self.snippet_store = SnippetStore(db)
        self.ai_service = AIService()
        self.db = db

    async def get_ts_snippets_translated_data(
        self,
        ts_snippets: list[TranscriptSnippet],
        source_lang: Language,
        target_lang: Language,
    ):
        snippet_ids = [snippet.snippet_id for snippet in ts_snippets]

        existing_translations = (
            await self.snippet_translation_store.get_snippet_translations_by_lang(
                snippet_ids,
                target_lang.id,
            )
        )

        if existing_translations:
            return await self.get_normalized_ts_translated_snippets(
                ts_snippets,
                existing_translations,
                source_lang,
                target_lang,
            )

        snippets_with_no_saved_words = (
            await self.snippet_store.get_snippets_by_ids_with_no_saved_words(snippet_ids)
        )

        if snippets_with_no_saved_words:
            await self.generate_snippet_translations_and_word_translations(
                snippets_with_no_saved_words,
                source_lang,
                target_lang,
            )
        else:
            await self.generate_snippet_translations_and_word_translations_for_existing_snippet_words(
                [ts_snippet.snippet for ts_snippet in ts_snippets],
                target_lang,
            )

        await self.db.commit()

        snippet_translations = (
            await self.snippet_translation_store.get_snippet_translations_by_lang(
                snippet_ids,
                target_lang.id,
            )
        )

        return await self.get_normalized_ts_translated_snippets(
            ts_snippets,
            snippet_translations,
            source_lang,
            target_lang,
        )
    
    async def get_normalized_ts_translated_snippets(self, ts_snippets: List[TranscriptSnippet], snippets_translations: List[SnippetTranslation], source_lang: Language, target_lang: Language) -> List[Dict]:
        try:
            translation_map = {t.snippet_id: t for t in snippets_translations}
            words_by_snippet = defaultdict(list)
            snippet_words = await self.snippet_word_store.get_snippet_words_batch([s.snippet_id for s in ts_snippets])
            for sw in snippet_words:
                words_by_snippet[sw.snippet_id].append(sw)
            translations_by_word = defaultdict(list)
            word_translations = await self.word_translation_store.get_word_translations_batch_by_lang(
                [s.word_id for s in snippet_words],
                target_lang.id,
            )
            for t in word_translations:
                translations_by_word[t.word_id].append(t)
        
            normalized = []

            for ts_snippet in ts_snippets:
                snippet_translation = translation_map.get(ts_snippet.snippet_id)
                if snippet_translation is None:
                    raise ValueError(
                        f"Missing translation for snippet {ts_snippet.snippet_id}"
                    )

                normalized_snippet_words = [{
                    "text": w.text,
                    "part_of_speech": w.part_of_speech_tag,
                    "romanized": w.word.romanized,
                    "translations": [{"text": t.text} for t in translations_by_word[w.word_id]],
                    "order_index": w.order_index
                } for _, w in enumerate(words_by_snippet[ts_snippet.snippet_id])]
                
                normalized.append({
                    "snippet_id": ts_snippet.snippet_id,
                    "text": ts_snippet.snippet.text,
                    "translation": snippet_translation.text,
                    "source_lang_code": source_lang.code,
                    "target_lang_code": target_lang.code,
                    "start": ts_snippet.start,
                    "end": ts_snippet.end,
                    "duration": ts_snippet.duration,
                    "snippet_words": normalized_snippet_words
                })

            return normalized
        except Exception as e:
            raise RuntimeError(f"Error normalizing batched translated snippets. {e}") from e

    async def generate_snippet_translations_and_word_translations(
        self,
        snippets: list[Snippet],
        source_lang: Language,
        target_lang: Language,
    ):

        ai_data = []

        for snippet in snippets:
            result = await self.ai_service.fetch_ai_data(
                AIPromptType.SNIPPET_TRANSLATION,
                {
                    "target_lang_name": target_lang.name,
                },
                {
                    "snippet_id": snippet.id,
                    "text": snippet.text,
                },
            )
            ai_data.append(result)

        await self.snippet_translation_store.add_ai_snippet_translations_batch(
            ai_data,
            target_lang.id,
        )

        all_word_parts = self._get_all_word_parts(ai_data)

        word_map = await self.word_store.save_ai_words_batch(
            all_word_parts,
            source_lang.id,
        )

        self.snippet_word_store.add_ai_snippet_words_batch(
            ai_data,
            word_map,
            source_lang.id,
        )

        all_word_parts = [
            {
                **word_part,
                "word_id": word_map[(sanitize_word(word_part["word"]), source_lang.id)],
            }
            for word_part in all_word_parts
        ]

        await self.word_translation_store.add_ai_word_translations_batch(
            all_word_parts,
            target_lang.id,
        )

    async def generate_snippet_translations_and_word_translations_for_existing_snippet_words(
        self,
        snippets: list[Snippet],
        target_lang: Language,
    ):
        ai_data = []
        
        for snippet in snippets:
            result = await self.ai_service.fetch_ai_data(
                AIPromptType.SNIPPET_WORDS_TRANSLATION,
                {
                    "target_lang_name": target_lang.name,
                },
                {
                    "snippet_id": snippet.id,
                    "snippet_text": snippet.text,
                    "snippet_words": [
                        {
                            "word_id": sw.word_id,
                            "text": sw.word.text,
                        }
                        for sw in snippet.snippet_words
                    ],
                }
            )
            ai_data.append(result)

        await self.snippet_translation_store.add_ai_snippet_translations_batch(
            ai_data,
            target_lang.id,
        )

        all_word_parts = self._get_all_word_parts(ai_data)

        await self.word_translation_store.add_ai_word_translations_batch(
            all_word_parts,
            target_lang.id,
        )
    
    def _get_all_word_parts(self, ai_data):
        return [
            word_part
            for snippet in ai_data
            for word_part in snippet["word_parts"]
        ]