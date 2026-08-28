from sqlalchemy.orm import Session, selectinload
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select
from models import WordTranslation

class WordTranslationStore:
    def __init__(self, db: Session):
        self.db = db

    async def add_ai_word_translations_batch(
        self,
        data: list[dict],
        lang_id: int
    ):
        values = []
        for word in data:
            for translation in word["translations"]:
                values.append({
                    "word_id": word["word_id"],
                    "language_id": lang_id,
                    "text": translation,
                })
               
        stmt = (
            insert(WordTranslation)
            .values(values)
            .on_conflict_do_nothing(
                index_elements=["word_id", "language_id", "text"]
            )
        )

        await self.db.execute(stmt)

    async def get_word_translations_batch_by_lang(
        self,
        word_ids: list[int],
        lang_id: int,
        eager_load: bool = False,
    ) -> list[WordTranslation]:

        query = (
            select(WordTranslation)
            .where(
                WordTranslation.word_id.in_(word_ids),
                WordTranslation.language_id == lang_id,
            )
        )

        if eager_load:
            query = query.options(
                selectinload(WordTranslation.language),
                selectinload(WordTranslation.word),
            )

        result = await self.db.execute(query)
        return result.scalars().all()