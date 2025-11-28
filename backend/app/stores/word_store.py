from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from models import Word, Translation, SnippetType, SnippetWord
from app.utils.helpers import sanitize_word, is_latin_script
from app.stores.snippet_store import SnippetStore

class WordStore:
    def __init__(self, db: Session):
        self.db = db
        self.snippet_store = SnippetStore(db)

    async def get_word_by_lang(self, word_text: str, source_lang_id: int) -> Word:
        word_sanitized = sanitize_word(word_text)
        result = await self.db.execute(
            select(Word).where(
                Word.text == word_sanitized,
                Word.language_id == source_lang_id
            )
        )
        return result.scalars().first()

    async def save_snippet_words(self, words: list, snippet_type: SnippetType, snippet_id: int, source_lang_id: int, target_lang_id: int):
        for i, part in enumerate(words):
            word_id = await self.save_word(part, source_lang_id, target_lang_id)
            
            # separate logic below
            # if snippet_type == SnippetType.TRANSCRIPT:
                # ts_snippet = self.snippet_store.get_ts_snippet_by_id(snippet_id)
                # print(f"TS Snippet ID {ts_snippet.id} has {len(ts_snippet.snippet_words)} snippet words.")
                # if len(ts_snippet.snippet_words) > 0:
                #     continue
            # elif snippet_type == SnippetType.POS_EXAMPLE:
            #     snippet = self.snippet_store.get_snippet_by_id(snippet_id)
            #     if len(snippet.snippet_words) > 0:
            #         continue

            snippet_word = SnippetWord(
                text=part["word"].strip(),
                part_of_speech_tag=part["part_of_speech"],
                word_id=word_id,
                snippet_id=snippet_id if snippet_type == SnippetType.POS_EXAMPLE else None,
                transcript_snippet_id=snippet_id if snippet_type == SnippetType.TRANSCRIPT else None,
                order_index=i
            )
            self.db.add(snippet_word)

        await self.db.commit()

    async def save_word_translations(self, word: Word, translations: list, target_lang_id: int):
        for text in translations:
            stmt = insert(Translation).values(
                text=text,
                word_id=word.id,
                language_id=target_lang_id,
            ).on_conflict_do_nothing(
                index_elements=["word_id", "language_id", "text"]
            )
            await self.db.execute(stmt)

        await self.db.commit()

    async def save_word(self, data: object, source_lang_id: int, target_lang_id: int) -> Word:
        word = await self.get_word_by_lang(data["word"], source_lang_id)

        if word is None:
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
            await self.save_word_translations(word, data["translations"], target_lang_id)
            return word.id
            
        existing_translation_result = await self.db.execute(
            select(Translation).filter(
                Translation.word_id == word.id,
                Translation.language_id == target_lang_id
            )
        )
        existing_translation = existing_translation_result.scalars().first()

        if existing_translation is None:
            await self.save_word_translations(word, data["translations"], target_lang_id)
    
        return word.id
    
    def update_word(self, word: Word, data: dict):
        for key, value in data.items():
            # Only update attributes that actually exist on the Word model
            if hasattr(word, key):
                setattr(word, key, value)

        self.db.commit()
        self.db.refresh(word)
