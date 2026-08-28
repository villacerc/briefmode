from sqlalchemy.orm import Session, selectinload
from models import TranscriptSnippet, SnippetWord, Snippet
from app.utils.helpers import sanitize_snippet_text
from sqlalchemy import select

TRANSCRIPT_SNIPPET_QUERY_OPTIONS = (
    selectinload(TranscriptSnippet.snippet)
    .selectinload(Snippet.snippet_words)
    .selectinload(SnippetWord.word),
    selectinload(TranscriptSnippet.video),
)

class TranscriptSnippetStore:
    def __init__(self, db: Session):
        self.db = db

    async def get_ts_snippets_by_video_id(self, video_id: int, eager_load: bool = False) -> list[TranscriptSnippet]:
        query = select(TranscriptSnippet).where(TranscriptSnippet.video_id == video_id).order_by(TranscriptSnippet.start)
        if eager_load:
            query = query.options(*TRANSCRIPT_SNIPPET_QUERY_OPTIONS)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def add_ts_snippets(
        self,
        video_id: int,
        snippets: list[Snippet],
        fetched_data: list,
    ):
        new_ts_snippets = []

        for i, (snippet, data) in enumerate(zip(snippets, fetched_data)):
            end_time = (
                fetched_data[i + 1].start
                if i < len(fetched_data) - 1
                else data.start + data.duration
            )

            new_ts_snippets.append(
                TranscriptSnippet(
                    video_id=video_id,
                    snippet=snippet,
                    start=data.start,
                    end=end_time,
                    duration=data.duration,
                )
            )

        self.db.add_all(new_ts_snippets)