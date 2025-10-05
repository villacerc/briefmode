from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from models import Word, Translation
from app.utils.helpers import sanitize_word, is_latin_script

class WordStore:
    def __init__(self, db: Session):
        self.db = db

    def get_word_by_lang(self, word_text: str, lang_id: int) -> Word:
        word_sanitized = sanitize_word(word_text)
        return self.db.query(Word).filter(
            Word.text == word_sanitized,
            Word.language_id == lang_id
        ).first()

    def save_word(self, word_text: str, romanized: str, translations: list, source_lang_id: int, target_lang_id: int) -> Word:
        word_sanitized = sanitize_word(word_text)

        existing_word = self.get_word_by_lang(word_sanitized, source_lang_id)

        if existing_word:
            return existing_word

        new_word = Word(
            text=word_sanitized,
            romanized=romanized if not is_latin_script(word_sanitized) else "",
            language_id=source_lang_id
        )
        self.db.add(new_word)
        self.db.flush()

        for i, text in enumerate(translations): 
            stmt = insert(Translation).values(
                text=text,
                word_id=new_word.id,
                language_id=target_lang_id,
            ).on_conflict_do_nothing(
                index_elements=["word_id", "language_id", "text"]
            )
            self.db.execute(stmt)

        self.db.commit()
        self.db.refresh(new_word)

        return new_word
