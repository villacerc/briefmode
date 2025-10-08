# app/stores/translations_store.py
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from models import SnippetType, Translation, SnippetTranslation, TranscriptSnippet, Snippet, Language
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

    def get_snippet_translation_by_lang(self, snippet_id: int, lang_id: int) -> bool:
        return self.db.query(SnippetTranslation).filter(
            SnippetTranslation.snippet_id == snippet_id,
            SnippetTranslation.language_id == lang_id
        ).first()

    def save_snippet_translation(self, text: str, snippet: Snippet, translation_lang: Language) -> SnippetTranslation:
        snippet_translation = SnippetTranslation(
            text=text,
            snippet_id=snippet.id,
            language_id=translation_lang.id,
        )
        self.db.add(snippet_translation)
        self.db.commit()
        self.db.refresh(snippet_translation)
        return snippet_translation

    def save_ai_snippet_translation(self, snippet: Snippet, translation_lang: Language, data: dict) -> SnippetTranslation:
        snippet_translation = self.save_snippet_translation(data["translation"], snippet, translation_lang)
        self.word_store.save_snippet_words(data["word_parts"], SnippetType.POS_EXAMPLE, snippet.id, snippet.language_id, translation_lang.id)

        return snippet_translation

    def save_ai_ts_snippet_translation(self, ts_snippet: TranscriptSnippet, translation_lang: Language, data: dict) -> SnippetTranslation:
        snippet_translation = self.save_snippet_translation(data["translation"], ts_snippet.snippet, translation_lang)
        self.word_store.save_snippet_words(data["word_parts"], SnippetType.TRANSCRIPT, ts_snippet.id, ts_snippet.snippet.language_id, translation_lang.id)

        return snippet_translation
