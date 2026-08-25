from sqlalchemy.orm import Session, selectinload
from models import Snippet, Language
from app.utils.helpers import sanitize_snippet_text
from sqlalchemy import select

class SnippetStore:
    def __init__(self, db: Session):
        self.db = db

    async def get_snippet(self, text: str, language: Language) -> Snippet:
        snippet_text_sanitized = sanitize_snippet_text(text, language.code)
        result = await self.db.execute(
            select(Snippet).where(Snippet.text == snippet_text_sanitized)
        )
        return result.scalars().first()

    async def get_snippet_by_id(self, snippet_id: int) -> Snippet:
        result = await self.db.execute(
            select(Snippet).where(Snippet.id == snippet_id)
            .options(
                selectinload(Snippet.snippet_words)
            )
        )
        return result.scalars().first()

    async def get_snippets_by_ids_with_no_saved_words(self, snippet_ids: list[int]):
        query = select(Snippet).where(
            Snippet.id.in_(snippet_ids),
            ~Snippet.snippet_words.any(),
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def save_snippet(self, text: str, source_lang: Language) -> Snippet:
        existing_snippet = await self.get_snippet(text, source_lang)
        if existing_snippet:
            return existing_snippet.id

        new_snippet = Snippet(
            text=sanitize_snippet_text(text, source_lang.code)
        )
        self.db.add(new_snippet)
        await self.db.commit()

        return new_snippet.id

    async def add_snippets(
        self,
        fetched_data: list,
    ) -> list[Snippet]:

        new_snippets = [
            Snippet(text=snippet.text)
            for snippet in fetched_data
        ]

        self.db.add_all(new_snippets)

        return new_snippets

        