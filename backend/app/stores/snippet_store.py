from sqlalchemy.orm import Session, selectinload
from models import Snippet, Language
from app.utils.helpers import sanitize_snippet_text
from sqlalchemy import select

class SnippetStore:
    def __init__(self, db: Session):
        self.db = db

    async def get_snippet_by_text(self, text: str, eager_load: bool = False) -> Snippet:
        query = select(Snippet).where(Snippet.text == text)
        if eager_load:
            query = query.options(
                selectinload(Snippet.language),
                selectinload(Snippet.snippet_words)
            )
        
        result = await self.db.execute(query)

        return result.scalars().first()

    async def get_snippets_by_ids_with_no_saved_words(self, snippet_ids: list[int]):
        query = select(Snippet).where(
            Snippet.id.in_(snippet_ids),
            ~Snippet.snippet_words.any(),
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def add_snippets(
        self,
        texts: list[str],
        lang_id: int,
    ) -> list[Snippet]:

        new_snippets = [
            Snippet(text=text, language_id=lang_id)
            for text in texts
        ]

        self.db.add_all(new_snippets)

        await self.db.flush()

        return new_snippets

        