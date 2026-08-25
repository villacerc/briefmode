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

    async def get_snippet_translations_by_lang(self, ts_snippet_ids: list[int], lang_id: int, eager_load: bool = False) -> list[SnippetTranslation]:
        query = (
            select(SnippetTranslation)
            .filter(
                SnippetTranslation.snippet_id.in_(ts_snippet_ids),
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

    async def get_snippet_translation_by_lang_old(self, snippet_id: int, lang_id: int, eager_load: bool = False) -> SnippetTranslation:
        query = select(SnippetTranslation).filter(
                SnippetTranslation.snippet_id == snippet_id,
                SnippetTranslation.language_id == lang_id
            )
        if eager_load:
            query = query.options(
                selectinload(SnippetTranslation.language),
                selectinload(SnippetTranslation.snippet)
            )

        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_snippet_translation_by_id(self, snippet_translation_id: int, eager_load: bool = False) -> SnippetTranslation:
        query = select(SnippetTranslation).where(SnippetTranslation.id == snippet_translation_id)
        if eager_load:
            query = query.options(
                selectinload(SnippetTranslation.language),
                selectinload(SnippetTranslation.snippet)
            )

        result = await self.db.execute(query)
        return result.scalars().first()