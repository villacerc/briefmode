from sqlalchemy.orm import Session
from models import Snippet
from app.utils.helpers import sanitize_phrase

class SnippetStore:
    def __init__(self, db: Session):
        self.db = db

    def get_snippet_by_lang(self, text: str, lang_id: int) -> Snippet:
        snippet_sanitized = sanitize_phrase(text)
        return self.db.query(Snippet).filter(
            Snippet.text == snippet_sanitized,
            Snippet.language_id == lang_id
        ).first()

    def save_snippet(self, text: str, source_lang_id: int) -> Snippet:
        existing_snippet = self.get_snippet_by_lang(text, source_lang_id)

        if existing_snippet:
            return existing_snippet

        new_snippet = Snippet(
            text=sanitize_phrase(text),
            language_id=source_lang_id
        )
        self.db.add(new_snippet)
        self.db.commit()
        self.db.refresh(new_snippet)

        return new_snippet
