from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models import Video, TranscriptSnippet, Snippet, SnippetWord, Word, Language
from app.stores.snippet_store import SnippetStore

class VideoStore:
    def __init__(self, db):
        self.db = db
        self.snippet_store = SnippetStore(db)

    async def get_video_by_id(self, video_id: int):
        result = await self.db.execute(select(Video).options(selectinload(Video.language)).where(Video.id == video_id))
        return result.scalars().first()
    
    async def get_video_by_source_id(self, source_id: str):
        result = await self.db.execute(select(Video).options(selectinload(Video.language)).where(Video.source_id == source_id))
        return result.scalars().first()

    async def save_video(self, data: dict):
        video = Video(source_id=data["source_id"], title=data["title"], language_id=data["language_id"])
        self.db.add(video)
        await self.db.commit()
        return video.id

    def get_transcript_snippets(self, source_id: str):
        video = self.db.execute(
            select(Video).options(
                selectinload(Video.transcript_snippets)
                    .selectinload(TranscriptSnippet.snippet_words)
                    .selectinload(SnippetWord.word),
                selectinload(Video.transcript_snippets)
                    .selectinload(TranscriptSnippet.video),
            )
            .where(Video.source_id == source_id)
        ).scalars().first()

        if video and video.transcript_snippets:
            return video.transcript_snippets
        return None

    def save_transcript_snippets(self, source_id: str, source_lang: Language, transcript_data):
        video = self.get_video_by_source_id(source_id)
        if not video:
            raise ValueError(f"Video with source_id '{source_id}' not found.")

        for i, item in enumerate(transcript_data.snippets):
            snippet = self.snippet_store.save_snippet(item.text, source_lang)

            end_time = transcript_data[i + 1].start if i < len(transcript_data) - 1 else item.start + item.duration
            self.snippet_store.save_ts_snippet(video_id=video.id, snippet_id=snippet.id, data=item, end_time=end_time)