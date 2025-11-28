from sqlalchemy.orm import Session, selectinload
from models import Snippet, Language, TranscriptSnippet, SnippetWord
from app.utils.helpers import sanitize_snippet
from sqlalchemy import select

class SnippetStore:
    def __init__(self, db: Session):
        self.db = db

    async def get_snippet(self, text: str, language: Language) -> Snippet:
        snippet_sanitized = sanitize_snippet(text, language.code)
        result = await self.db.execute(
            select(Snippet).where(Snippet.text == snippet_sanitized)
        )
        return result.scalars().first()

    def get_snippet_by_id(self, snippet_id: int) -> Snippet:
        return self.db.query(Snippet).filter(Snippet.id == snippet_id).first()

    def get_ts_snippet_by_id(self, ts_snippet_id: int) -> TranscriptSnippet:
        return (
            self.db.query(TranscriptSnippet)
            .options(
                selectinload(TranscriptSnippet.snippet_words)
                .selectinload(SnippetWord.word)
            )
            .filter(TranscriptSnippet.id == ts_snippet_id)
            .first()
        )
        
    async def save_ts_snippet(self, video_id: int, snippet_id: int, data: dict, end_time: float) -> TranscriptSnippet:
        existing_ts_snippet_result = await self.db.execute(
            select(TranscriptSnippet).filter(
                TranscriptSnippet.video_id == video_id,
                TranscriptSnippet.start == data.start,
            )
        )
        existing_ts_snippet = existing_ts_snippet_result.scalars().first()
        if existing_ts_snippet:
            return existing_ts_snippet.id

        ts_snippet = TranscriptSnippet(
            video_id=video_id,
            snippet_id=snippet_id,
            text=data.text,
            start=data.start,
            end=end_time,
            duration=data.duration
        )
        self.db.add(ts_snippet)
        await self.db.commit()
        return ts_snippet.id

    async def save_snippet(self, text: str, source_lang: Language) -> Snippet:
        existing_snippet = await self.get_snippet(text, source_lang)
        if existing_snippet:
            return existing_snippet.id

        new_snippet = Snippet(
            text=sanitize_snippet(text, source_lang.code)
        )
        self.db.add(new_snippet)
        await self.db.commit()

        return new_snippet.id
