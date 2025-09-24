# app/stores/translations_store.py
from sqlalchemy.orm import Session
from models import Word, Translation, TranslationSnippet

class TranslationStore:
    def __init__(self, db: Session):
        self.db = db

    def get_translations_by_snippet_and_language(self, snippet_id: int, lang_id: int) -> bool:
        return self.db.query(Translation).join(Word).filter(
            Word.transcript_snippet_id == snippet_id,
            Translation.language_id == lang_id
        ).all()

    def get_translation_snippet_by_language(self, snippet_id: int, lang_id: int) -> bool:
        return self.db.query(TranslationSnippet).filter(
            TranslationSnippet.transcript_snippet_id == snippet_id,
            TranslationSnippet.language_id == lang_id
        ).first()

    def save_translation(self, snippet_id: int, lang_id: int, parsed_json: dict):
        # Save translation snippet
        transcript_snippet = TranslationSnippet(
            text=parsed_json.get("translation", ""),
            transcript_snippet_id=snippet_id,
            language_id=lang_id,
        )
        self.db.add(transcript_snippet)
        self.db.commit()
        self.db.refresh(transcript_snippet)

        # Save words & translations
        for i, part in enumerate(parsed_json.get("word_parts", [])):
            word = Word(
                text=part["word"],
                romanized=part["romanized"],
                transcript_snippet_id=snippet_id,
                order_index=i
            )
            self.db.add(word)
            self.db.commit()
            self.db.refresh(word)
            for j, tpart in enumerate(part.get("translations", [])):
                translation = Translation(
                    text=tpart["translation"],
                    word_id=word.id,
                    language_id=lang_id,
                    order_index=j
                )
                self.db.add(translation)
        self.db.commit()
