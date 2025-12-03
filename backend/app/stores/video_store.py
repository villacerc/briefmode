from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models import Video, TranscriptSnippet, Snippet, SnippetWord, Word, Language

class VideoStore:
    def __init__(self, db):
        self.db = db

    async def get_video_by_id(self, video_id: int):
        result = await self.db.execute(select(Video).options(selectinload(Video.language)).where(Video.id == video_id))
        return result.scalars().first()
    
    async def get_video_by_source_id(self, source_id: str):
        result = await self.db.execute(select(Video).options(selectinload(Video.language)).where(Video.source_id == source_id))
        return result.scalars().first()

    async def save_video(self, data: dict):
        source_id = data["source_id"]
        existing_video = await self.get_video_by_source_id(source_id)
        if existing_video:
            return existing_video.id
            
        video = Video(source_id=data["source_id"], title=data["title"], language_id=data["language_id"])
        self.db.add(video)
        await self.db.commit()
        return video.id