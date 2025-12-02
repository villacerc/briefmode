from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from models import Word, Translation, SnippetType, SnippetWord
from app.utils.helpers import sanitize_word, is_latin_script
from .snippet_store import SnippetStore

class WordStore:
    def __init__(self, db: Session):
        self.db = db
        self.snippet_store = SnippetStore(db)

    async def get_snippet_words(self, snippet_type: SnippetType, snippet_id: int) -> list:
        if snippet_type == SnippetType.POS_EXAMPLE:
            query = select(SnippetWord).where(SnippetWord.snippet_id == snippet_id).order_by(SnippetWord.order_index)
        else:
            query = select(SnippetWord).where(SnippetWord.transcript_snippet_id == snippet_id).order_by(SnippetWord.order_index)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_word_by_lang(self, word_text: str, source_lang_id: int) -> Word:
        word_sanitized = sanitize_word(word_text)
        result = await self.db.execute(
            select(Word).where(
                Word.text == word_sanitized,
                Word.language_id == source_lang_id
            )
            .options(selectinload(Word.language))
        )
        return result.scalars().first()

    async def save_snippet_word(self, data: object, word_id: int, index: int, snippet_type: SnippetType, snippet_id: int):
        snippet_word = SnippetWord(
            text=data["word"].strip(),
            part_of_speech_tag=data["part_of_speech"],
            word_id=word_id,
            snippet_id=snippet_id if snippet_type == SnippetType.POS_EXAMPLE else None,
            transcript_snippet_id=snippet_id if snippet_type == SnippetType.TRANSCRIPT else None,
            order_index=index
        )
        self.db.add(snippet_word)
        await self.db.commit()
        return snippet_word.id

    async def save_snippet_words(self, words: list, snippet_type: SnippetType, snippet_id: int, source_lang_id: int, target_lang_id: int):
        existing_snippet_words = await self.get_snippet_words(snippet_type, snippet_id)

        for i, part in enumerate(words):
            word_id = await self.save_word(part, source_lang_id, target_lang_id)

            await self.save_word_translations(word_id, part["translations"], target_lang_id)

            if not existing_snippet_words:
                await self.save_snippet_word(part, word_id, i, snippet_type, snippet_id)

    async def save_word_translations(self, word_id: int, translations: list, target_lang_id: int):
        existing_translation_result = await self.db.execute(
            select(Translation).where(
                Translation.word_id == word_id,
                Translation.language_id == target_lang_id
            )
        )
        existing_translation = existing_translation_result.scalars().first()
        if existing_translation:
            return

        for text in translations:
            stmt = insert(Translation).values(
                text=text,
                word_id=word_id,
                language_id=target_lang_id,
            ).on_conflict_do_nothing(
                index_elements=["word_id", "language_id", "text"]
            )
            await self.db.execute(stmt)

        await self.db.commit()

    async def save_word(self, data: object, source_lang_id: int, target_lang_id: int) -> int:
        existing_word = await self.get_word_by_lang(data["word"], source_lang_id)
        if existing_word:
            return existing_word.id

        word_sanitized = sanitize_word(data["word"])
        romanized_sanitized = sanitize_word(data["romanized"])
        word = Word(
            text=word_sanitized,
            romanized=romanized_sanitized if not is_latin_script(word_sanitized) else "",
            phonetic_spelling=data["phonetic_spelling"],
            language_id=source_lang_id
        )
        self.db.add(word)
        await self.db.commit()
        return word.id
     
    def update_word(self, word: Word, data: dict):
        for key, value in data.items():
            # Only update attributes that actually exist on the Word model
            if hasattr(word, key):
                setattr(word, key, value)

        self.db.commit()
        self.db.refresh(word)
