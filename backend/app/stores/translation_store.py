# app/stores/translations_store.py
from typing import List
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.dialects.postgresql import insert
from models import SnippetType, Translation, SnippetTranslation, TranscriptSnippet, Snippet, Language, SnippetWord, Word
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

    def get_ts_snippet_by_translated_lang(self, ts_snippet_id: int, target_lang_id: int) -> TranscriptSnippet:
        ts_snippet = (
            self.db.query(TranscriptSnippet)
            .options(
                selectinload(TranscriptSnippet.snippet_words)
                .selectinload(SnippetWord.word)
            )
            .filter(TranscriptSnippet.id == ts_snippet_id)
            .first()
        )

        snippet_word_ids = [sw.word_id for sw in ts_snippet.snippet_words]
        
        snippet_translations = (
            self.db.query(SnippetTranslation)
            .filter(
                SnippetTranslation.snippet_id == ts_snippet.snippet.id,
                SnippetTranslation.language_id == target_lang_id
            )
            .all()
        )

        # avoid modifying the original loaded relationships 
        object.__setattr__(ts_snippet.snippet, "translations", snippet_translations)

        word_translations = (
            self.db.query(Translation)
            .filter(
                Translation.word_id.in_(snippet_word_ids),
                Translation.language_id == target_lang_id
            )
            .all()
        )

        word_trans_map = {}
        for t in word_translations:
            word_trans_map.setdefault(t.word_id, []).append(t)

        for sw in ts_snippet.snippet_words:
            # avoid modifying the original loaded relationships 
            object.__setattr__(sw.word, "translations", word_trans_map.get(sw.word_id, []))

        return ts_snippet

    def get_snippet_translation_by_lang(self, snippet_id: int, lang_id: int) -> SnippetTranslation:
        return self.db.query(SnippetTranslation).filter(
            SnippetTranslation.snippet_id == snippet_id,
            SnippetTranslation.language_id == lang_id
        ).first()

    def save_snippet_translation(self, text: str, snippet: Snippet, target_lang: Language) -> SnippetTranslation:
        existing_snippet_translation = self.get_snippet_translation_by_lang(snippet.id, target_lang.id)
        if existing_snippet_translation:
            return existing_snippet_translation

        snippet_translation = SnippetTranslation(
            text=text,
            snippet_id=snippet.id,
            language_id=target_lang.id,
        )
        self.db.add(snippet_translation)
        self.db.commit()
        self.db.refresh(snippet_translation)

        return snippet_translation

    def save_ai_snippet_translation(self, snippet: Snippet, target_lang: Language, data: dict) -> SnippetTranslation:
        snippet_translation = self.save_snippet_translation(data["translation"], snippet, target_lang)

        self.word_store.save_snippet_words(data["word_parts"], SnippetType.POS_EXAMPLE, snippet.id, snippet.dictionary_pos.language_id, target_lang.id)
        
        self.db.refresh(snippet)

        return snippet_translation

    def save_ai_ts_snippet_translation(self, ts_snippet: TranscriptSnippet, target_lang: Language, data: dict) -> SnippetTranslation:
        snippet_translation = self.save_snippet_translation(data["translation"], ts_snippet.snippet, target_lang)

        self.word_store.save_snippet_words(data["word_parts"], SnippetType.TRANSCRIPT, ts_snippet.id, ts_snippet.video.language_id, target_lang.id)

        return snippet_translation
