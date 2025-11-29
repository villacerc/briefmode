from typing import List
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.dialects.postgresql import insert
from models import SnippetType, Translation, SnippetTranslation, TranscriptSnippet, Snippet, Language, SnippetWord, Word
from app.utils.helpers import sanitize_word
from .word_store import WordStore
from .video_store import VideoStore

from sqlalchemy import select

class TranslationStore:
    def __init__(self, db: Session):
        self.db = db
        self.word_store = WordStore(db)
        self.video_store = VideoStore(db)

    async def get_snippet_translation(self, snippet_id: int, lang_id: int) -> list:
        result = await self.db.execute(
            select(SnippetTranslation).where(
                SnippetTranslation.snippet_id == snippet_id,
                SnippetTranslation.language_id == lang_id
            )
        )
        return result.scalars().first()

    async def get_word_translations(self, word_id: int, lang_id: int) -> List[Translation]:
        result = await self.db.execute(
            select(Translation).where(
                Translation.word_id == word_id,
                Translation.language_id == lang_id
            )
        )
        return result.scalars().all()

    async def get_loaded_translated_ts_snippet(self, ts_snippet_id: int, target_lang_id: int) -> TranscriptSnippet:
        ts_snippet_result = await self.db.execute(
            select(TranscriptSnippet)
            .options(
                selectinload(TranscriptSnippet.snippet_words)
                    .selectinload(SnippetWord.word),
                selectinload(TranscriptSnippet.snippet)
                    .selectinload(Snippet.translations)
            )
            .where(TranscriptSnippet.id == ts_snippet_id)
        )
        ts_snippet = ts_snippet_result.scalars().first()

        snippet_word_ids = [sw.word_id for sw in ts_snippet.snippet_words]
        
        snippet_translations_result = await self.db.execute(
            select(SnippetTranslation).filter(
                SnippetTranslation.snippet_id == ts_snippet.snippet.id,
                SnippetTranslation.language_id == target_lang_id
            )
        )
        snippet_translations = snippet_translations_result.scalars().all()

        # avoid modifying the original loaded relationships 
        object.__setattr__(ts_snippet.snippet, "translations", snippet_translations)

        word_translations_result = await self.db.execute(
            select(Translation).filter(
                Translation.word_id.in_(snippet_word_ids),
                Translation.language_id == target_lang_id
            )
        )
        word_translations = word_translations_result.scalars().all()

        word_trans_map = {}
        for t in word_translations:
            word_trans_map.setdefault(t.word_id, []).append(t)

        for sw in ts_snippet.snippet_words:
            # avoid modifying the original loaded relationships 
            object.__setattr__(sw.word, "translations", word_trans_map.get(sw.word_id, []))

        return ts_snippet

    async def get_snippet_translation_by_lang(self, snippet_id: int, lang_id: int) -> SnippetTranslation:
        result = await self.db.execute(
            select(SnippetTranslation).filter(
                SnippetTranslation.snippet_id == snippet_id,
                SnippetTranslation.language_id == lang_id
            )
        )
        return result.scalars().first()

    async def save_snippet_translation(self, text: str, snippet_id: int, target_lang: Language) -> SnippetTranslation:
        existing_snippet_translation = await self.get_snippet_translation_by_lang(snippet_id, target_lang.id)
        if existing_snippet_translation:
            return existing_snippet_translation.id

        snippet_translation = SnippetTranslation(
            text=text,
            snippet_id=snippet_id,
            language_id=target_lang.id,
        )
        self.db.add(snippet_translation)
        await self.db.commit()

        return snippet_translation.id

    def save_ai_snippet_translation(self, snippet: Snippet, target_lang: Language, data: dict) -> SnippetTranslation:
        snippet_translation = self.save_snippet_translation(data["translation"], snippet, target_lang)

        self.word_store.save_snippet_words(data["word_parts"], SnippetType.POS_EXAMPLE, snippet.id, snippet.dictionary_pos.language_id, target_lang.id)
        
        self.db.refresh(snippet)

        return snippet_translation

    async def save_ai_ts_snippet_translation(self, ts_snippet: TranscriptSnippet, target_lang: Language, data: dict) -> SnippetTranslation:
        video = await self.video_store.get_video_by_id(ts_snippet.video_id)
        source_lang = video.language

        await self.word_store.save_snippet_words(data["word_parts"], SnippetType.TRANSCRIPT, ts_snippet.id, source_lang.id, target_lang.id)
        
        snippet_translation_id = await self.save_snippet_translation(data["translation"], ts_snippet.snippet_id, target_lang)
        return snippet_translation_id


