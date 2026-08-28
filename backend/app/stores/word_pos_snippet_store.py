from models import WordPOSSnippet, Snippet, Word, SnippetWord
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.services.ai_service import AIService

WORD_POS_SNIPPET_QUERY_OPTIONS = (
    selectinload(WordPOSSnippet.snippet)
        .selectinload(Snippet.snippet_words)
        .selectinload(SnippetWord.word),
    selectinload(WordPOSSnippet.word)
        .selectinload(Word.language),
)

class WordPOSSnippetStore:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()

    async def get_word_pos_snippets(self, word_id: int, eager_load: bool = False) -> list[WordPOSSnippet]:
        query = (
            select(WordPOSSnippet)
            .where(
                WordPOSSnippet.word_id == word_id,
            )
        )

        if eager_load:
            query = query.options(*WORD_POS_SNIPPET_QUERY_OPTIONS)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def add_word_pos_snippets_batch(self, word_id, snippets, pos_data):
        values = []
        for i, (snippet, data) in enumerate(zip(snippets, pos_data)):
            values.append({
                "word_id": word_id,
                "snippet_id": snippet.id,
                "name": data["part_of_speech"],
                "description": data["definition"]
            })
            
        stmt = (
            insert(WordPOSSnippet)
            .values(values)
            .on_conflict_do_nothing(
                index_elements=["word_id", "name"]
            )
        )

        await self.db.execute(stmt)