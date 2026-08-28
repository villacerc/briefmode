from sqlalchemy.orm import Session, selectinload
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from models import SnippetTranslation

class SnippetTranslationStore:
    def __init__(self, db: Session):
        self.db = db

    async def add_ai_snippet_translations_batch(
        self,
        data: list[dict],
        lang_id: int
    ):
        values = []
        for snippet in data:
            values.append({
                "snippet_id": snippet["snippet_id"],
                "text": snippet["translation"],
                "language_id": lang_id,
            })
            
        stmt = (
            insert(SnippetTranslation)
            .values(values)
            .on_conflict_do_nothing(
                index_elements=["snippet_id", "language_id"]
            )
        )

        await self.db.execute(stmt)

    async def get_snippet_translations_by_lang(self, snippet_ids: list[int], lang_id: int, eager_load: bool = False) -> list[SnippetTranslation]:
        query = (
            select(SnippetTranslation)
            .filter(
                SnippetTranslation.snippet_id.in_(snippet_ids),
                SnippetTranslation.language_id == lang_id
            )
        )

        if eager_load:
            query = query.options(
                selectinload(SnippetTranslation.language),
                selectinload(SnippetTranslation.snippet)
            )

        result = await self.db.execute(query)
        return result.scalars().all()