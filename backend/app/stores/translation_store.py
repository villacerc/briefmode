# app/stores/translations_store.py
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from models import Word, Translation, SnippetTranslation, SnippetWord, TranscriptSnippet
from app.services.helpers import sanitize_word

class TranslationStore:
    def __init__(self, db: Session):
        self.db = db

    def get_snippet_translation_by_language(self, snippet_id: int, lang_id: int) -> bool:
        return self.db.query(SnippetTranslation).filter(
            SnippetTranslation.snippet_id == snippet_id,
            SnippetTranslation.language_id == lang_id
        ).first()

    def save_translation(self, ts_snippet: TranscriptSnippet, translation_lang_id: int, parsed_json: dict):
        # Save translation snippet
        snippet_translation = SnippetTranslation(
            text=parsed_json.get("translation", ""),
            snippet_id=ts_snippet.snippet_id,
            language_id=translation_lang_id,
        )
        self.db.add(snippet_translation)
        self.db.flush()

        # Save words & translations
        for i, part in enumerate(parsed_json.get("word_parts", [])):
            source_lang_id = ts_snippet.snippet.language_id
            word = self.save_word(part["word"], part["romanized"], part.get("translations", []), source_lang_id, translation_lang_id)

            snippet_word = SnippetWord(
                text=part["word"],
                part_of_speech=part.get("part_of_speech", ""),
                word_id=word.id,
                snippet_id=ts_snippet.snippet_id,
                order_index=i
            )
            self.db.add(snippet_word)
            self.db.flush()

        self.db.commit()
        return snippet_translation

    def save_word(self, word_text: str, romanized: str, translations: list, source_lang_id, translation_lang_id) -> Word:
        word_sanitized = sanitize_word(word_text)

        existing_word = self.db.query(Word).filter(
            Word.text == word_sanitized,
            Word.language_id == source_lang_id
        ).first()

        if existing_word:
            return existing_word

        new_word = Word(
            text=word_sanitized,
            romanized=romanized,
            language_id=source_lang_id
        )
        self.db.add(new_word)
        self.db.flush()

        for i, t in enumerate(translations): 
            stmt = insert(Translation).values(
                text=t["translation"],
                word_id=new_word.id,
                language_id=translation_lang_id,
                order_index=i
            ).on_conflict_do_nothing(
                index_elements=["word_id", "language_id", "text"]
            )
            self.db.execute(stmt)

        self.db.commit()
        self.db.refresh(new_word)

        return new_word
