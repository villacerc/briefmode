from typing import List
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.dialects.postgresql import insert
from models import SnippetType, WordTranslation, SnippetTranslation, TranscriptSnippet, Snippet, Language, SnippetWord, Word
from app.utils.helpers import sanitize_word
from .word_store import WordStore
from .video_store import VideoStore

from sqlalchemy import select

class TranslationStore:
    def __init__(self, db: Session):
        self.db = db
        self.word_store = WordStore(db)
        self.video_store = VideoStore(db)

    async def get_word_translations_by_lang(self, word_id: int, lang_id: int) -> List[WordTranslation]:
        result = await self.db.execute(
            select(WordTranslation).where(
                WordTranslation.word_id == word_id,
                WordTranslation.language_id == lang_id
            )
        )
        return result.scalars().all()

    async def get_snippet_translation_by_lang(self, snippet_id: int, lang_id: int) -> SnippetTranslation:
        result = await self.db.execute(
            select(SnippetTranslation).filter(
                SnippetTranslation.snippet_id == snippet_id,
                SnippetTranslation.language_id == lang_id
            )
        )
        return result.scalars().first()
        
    async def get_snippet_translation_by_id(self, snippet_translation_id: int) -> SnippetTranslation:
        result = await self.db.execute(
            select(SnippetTranslation).where(SnippetTranslation.id == snippet_translation_id)
        )
        return result.scalars().first()

    async def save_word_translations(self, word_id: int, translations: list, target_lang_id: int):
        existing_translation_result = await self.db.execute(
            select(WordTranslation).where(
                WordTranslation.word_id == word_id,
                WordTranslation.language_id == target_lang_id
            )
        )
        existing_translation = existing_translation_result.scalars().first()
        if existing_translation:
            return

        for text in translations:
            stmt = insert(WordTranslation).values(
                text=text,
                word_id=word_id,
                language_id=target_lang_id,
            ).on_conflict_do_nothing(
                index_elements=["word_id", "language_id", "text"]
            )
            await self.db.execute(stmt)

        await self.db.commit()

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
    
    async def save_snippet_words_and_translations(self, word_parts: list[dict], snippet_type: SnippetType, snippet_id: int, source_lang: Language, target_lang: Language):
        existing_ts_snippet_words = await self.word_store.get_snippet_words(snippet_type, snippet_id)

        for i, part in enumerate(word_parts):
            word_id = await self.word_store.save_word(part, source_lang.id)

            await self.save_word_translations(word_id, part["translations"], target_lang.id)

            if not existing_ts_snippet_words:
                await self.word_store.save_snippet_word(part, word_id, i, snippet_type, snippet_id)

    async def save_ai_snippet_translation(self, snippet_id: int, source_lang: Language, target_lang: Language, data: dict) -> SnippetTranslation:
        await self.save_snippet_words_and_translations(data["word_parts"], SnippetType.POS_EXAMPLE, snippet_id, source_lang, target_lang)

        snippet_translation_id = await self.save_snippet_translation(data["translation"], snippet_id, target_lang)
        return snippet_translation_id

    async def save_ai_ts_snippet_translation(self, ts_snippet: TranscriptSnippet, target_lang: Language, data: dict) -> SnippetTranslation:
        video = await self.video_store.get_video_by_id(ts_snippet.video_id, eager_load=True)
        source_lang = video.language

        await self.save_snippet_words_and_translations(data["word_parts"], SnippetType.TRANSCRIPT, ts_snippet.id, source_lang, target_lang)
        
        snippet_translation_id = await self.save_snippet_translation(data["translation"], ts_snippet.snippet_id, target_lang)
        return snippet_translation_id


