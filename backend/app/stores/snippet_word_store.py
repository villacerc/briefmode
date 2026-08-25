from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from models import Word, SnippetType, SnippetWord
from app.utils.helpers import sanitize_word

class SnippetWordStore:
    def __init__(self, db: Session):
        self.db = db

    async def get_snippet_words_batch(
        self,
        snippet_ids: list[int],
    ):
        result = await self.db.execute(
            select(SnippetWord)
            .where(
                SnippetWord.snippet_id.in_(snippet_ids)
            )
            .options(selectinload(SnippetWord.word))
            .order_by(
                SnippetWord.snippet_id,
                SnippetWord.order_index
            )
        )

        return result.scalars().all()

    async def get_snippet_words(self, snippet_type: SnippetType, snippet_id: int, eager_load: bool = False) -> list:
        query = select(SnippetWord).where(SnippetWord.snippet_id == snippet_id).order_by(SnippetWord.order_index)
        if eager_load:
            query = query.options(
                selectinload(SnippetWord.word)
                .selectinload(Word.language),
                selectinload(SnippetWord.snippet),
                selectinload(SnippetWord.transcript_snippet)
            )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def save_snippet_word(self, data: object, word_id: int, index: int, snippet_type: SnippetType, snippet_id: int):
        snippet_word = SnippetWord(
            text=data["word"].strip(),
            part_of_speech_tag=data["part_of_speech"],
            word_id=word_id,
            snippet_id=snippet_id,
            order_index=index
        )
        self.db.add(snippet_word)
        await self.db.commit()
        return snippet_word.id

    def add_snippet_words_batch(self, data: dict, word_map: dict, source_lang_id: int):
        snippet_words = []
        for snippet in data:
     
            for order_index, part in enumerate(snippet["word_parts"]):
                word_id = word_map[
                    (sanitize_word(part["word"]), source_lang_id)
                ]
                snippet_words.append(
                    SnippetWord(
                        snippet_id=snippet["snippet_id"],
                        word_id=word_id,
                        text=part["word"].strip(),
                        part_of_speech_tag=part["part_of_speech"],
                        order_index=order_index,
                    )
                )

        self.db.add_all(snippet_words)