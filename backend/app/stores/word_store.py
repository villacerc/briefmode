from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from models import Word, SnippetType, SnippetWord
from app.utils.helpers import sanitize_word, is_latin_script

class WordStore:
    def __init__(self, db: Session):
        self.db = db

    async def get_snippet_words(self, snippet_type: SnippetType, snippet_id: int) -> list:
        if snippet_type == SnippetType.POS_EXAMPLE:
            query = select(SnippetWord).where(SnippetWord.snippet_id == snippet_id).order_by(SnippetWord.order_index)
        else:
            query = select(SnippetWord).where(SnippetWord.transcript_snippet_id == snippet_id).order_by(SnippetWord.order_index)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_word_by_id(self, word_id: int) -> Word:
        result = await self.db.execute(
            select(Word).where(Word.id == word_id).options(selectinload(Word.language))
        )
        return result.scalars().first()

    async def get_word_by_text_and_lang(self, word_text: str, source_lang_id: int) -> Word:
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