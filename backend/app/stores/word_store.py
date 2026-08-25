from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from models import Word
from app.utils.helpers import sanitize_word, is_latin_script

class WordStore:
    def __init__(self, db: Session):
        self.db = db

    async def get_word_by_id(self, word_id: int, eager_load: bool = False) -> Word:
        query = select(Word).where(Word.id == word_id)
        if eager_load:
            query = query.options(selectinload(Word.language))

        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_word_by_text_and_lang(self, word_text: str, source_lang_id: int, eager_load: bool = False) -> Word:
        word_sanitized = sanitize_word(word_text)
        query = select(Word).where(
            Word.text == word_sanitized,
            Word.language_id == source_lang_id
        )
        if eager_load:
            query = query.options(selectinload(Word.language))

        result = await self.db.execute(query)
        return result.scalars().first()

    async def save_words_batch(self, word_parts: list[dict], source_lang_id: int) -> dict[tuple[str, int], int]:
        unique_words = {}
        for part in word_parts:
            sanitized_word = sanitize_word(part["word"])
            key = (sanitized_word, source_lang_id)
            unique_words[key] = {
                "language_id": source_lang_id,
                "text": sanitized_word,
                "romanized": part["romanized"],
                "phonetic_spelling": part["phonetic_spelling"],
            }
        values = list(unique_words.values())

        stmt = (
            insert(Word)
            .values(values)
            .on_conflict_do_update(
                index_elements=["text", "language_id"],
                set_={"text": Word.text},
            )
            .returning(
                Word.id,
                Word.text,
                Word.language_id,
            )
        )

        result = await self.db.execute(stmt)

        rows = result.fetchall()

        return {
            (row.text, row.language_id): row.id
            for row in rows
        }

    async def save_word(self, data: object, source_lang_id: int) -> int:
        existing_word = await self.get_word_by_text_and_lang(data["word"], source_lang_id)
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
     
    async def update_word(self, word: Word, data: dict):
        for key, value in data.items():
            # Only update attributes that actually exist on the Word model
            if hasattr(word, key):
                setattr(word, key, value)

        await self.db.commit()
        await self.db.refresh(word)