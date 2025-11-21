from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from models import Word, Translation, SnippetType, SnippetWord
from app.utils.helpers import sanitize_word, is_latin_script
from app.stores.snippet_store import SnippetStore

class WordStore:
    def __init__(self, db: Session):
        self.db = db
        self.snippet_store = SnippetStore(db)

    def get_word_by_lang(self, word_text: str, source_lang_id: int) -> Word:
        word_sanitized = sanitize_word(word_text)
        return self.db.query(Word).filter(
            Word.text == word_sanitized,
            Word.language_id == source_lang_id
        ).first()

    def save_snippet_words(self, words: list, snippet_type: SnippetType, snippet_id: int, source_lang_id: int, target_lang_id: int) -> list:
        snippet = self.snippet_store.get_snippet_by_id(snippet_id)
        if snippet and snippet.snippet_words:
            return snippet.snippet_words

        snippet_words = []
        for i, part in enumerate(words):
            word = self.save_word(part, source_lang_id, target_lang_id)

            snippet_word = SnippetWord(
                text=part["word"].strip(),
                part_of_speech_tag=part["part_of_speech"],
                word_id=word.id,
                snippet_id=snippet_id if snippet_type == SnippetType.POS_EXAMPLE else None,
                transcript_snippet_id=snippet_id if snippet_type == SnippetType.TRANSCRIPT else None,
                order_index=i
            )
            self.db.add(snippet_word)
            self.db.flush()
            snippet_words.append(snippet_word)

        self.db.commit()
        return snippet_words

    def save_word(self, data: object, source_lang_id: int, target_lang_id: int) -> Word:
        existing_word = self.get_word_by_lang(data["word"], source_lang_id)

        if existing_word:
            return existing_word

        word_sanitized = sanitize_word(data["word"])
        romanized_sanitized = sanitize_word(data["romanized"])
        new_word = Word(
            text=word_sanitized,
            romanized=romanized_sanitized if not is_latin_script(word_sanitized) else "",
            phonetic_spelling=data["phonetic_spelling"],
            language_id=source_lang_id
        )
        self.db.add(new_word)
        self.db.flush()

        for i, text in enumerate(data["translations"]):
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
    
    def update_word(self, word: Word, data: dict):
        for key, value in data.items():
            # Only update attributes that actually exist on the Word model
            if hasattr(word, key):
                setattr(word, key, value)

        self.db.commit()
        self.db.refresh(word)
