# app/stores/translations_store.py
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from models import Translation, SnippetTranslation, SnippetWord, TranscriptSnippet, Snippet, Language
from app.utils.helpers import sanitize_word
from .word_store import WordStore

class TranslationStore:
    def __init__(self, db: Session):
        self.db = db
        self.word_store = WordStore(db)
    
    def get_word_translations_by_lang(self, word_id: int, lang_id: int) -> List[Translation]:
        return self.db.query(Translation).filter(
            Translation.word_id == word_id,
            Translation.language_id == lang_id
        ).all()

    def get_snippet_translation_by_language(self, snippet_id: int, lang_id: int) -> bool:
        return self.db.query(SnippetTranslation).filter(
            SnippetTranslation.snippet_id == snippet_id,
            SnippetTranslation.language_id == lang_id
        ).first()

    def save_snippet_translation(self, snippet: Snippet, translation_lang: Language, parsed_json: dict):
        # Save translation snippet
        snippet_translation = SnippetTranslation(
            text=parsed_json.get("translation", ""),
            snippet_id=snippet.id,
            language_id=translation_lang.id,
        )
        self.db.add(snippet_translation)
        self.db.flush()

        # Save words & translations
        for i, part in enumerate(parsed_json.get("word_parts", [])):
            source_lang_id = snippet.language_id
            translation_lang_id = translation_lang.id   
            word = self.word_store.save_word(part["word"], part["romanized"], part.get("translations", []), source_lang_id, translation_lang_id)

            snippet_word = SnippetWord(
                text=part["word"],
                part_of_speech_tag=part["part_of_speech"],
                word_id=word.id,
                snippet_id=snippet.id,
                order_index=i
            )
            self.db.add(snippet_word)
            self.db.flush()

        self.db.commit()
        return snippet_translation
