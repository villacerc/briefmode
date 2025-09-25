from sqlalchemy import select
from sqlalchemy.orm import joinedload
from models import Video, TranscriptSnippet, Snippet

class VideoStore:
    def __init__(self, db):
        self.db = db

    def get_video(self, video_id: int):
        return self.db.query(Video).filter(Video.id == video_id).first()

    def get_transcript(self, source_id: str):
        video = self.db.execute(
            select(Video).options(joinedload(Video.transcript_snippets))
            .where(Video.source_id == source_id)
        ).scalars().first()

        if video and video.transcript_snippets:
            return video.transcript_snippets
        return None

    def save_transcript(self, source_id: str, language_id: int, transcript_data):
        video = Video(source_id=source_id)
        self.db.add(video)
        self.db.flush()

        transcript = []
        for i, item in enumerate(transcript_data.snippets):
            snippet = Snippet(language_id=language_id, text=item.text)
            self.db.add(snippet)
            self.db.flush()
            
            ts_snippet = TranscriptSnippet(
                video_id=video.id,
                snippet_id=snippet.id,
                start=item.start,
                end=transcript_data[i + 1].start if i < len(transcript_data) - 1 else item.start + item.duration,
                duration=item.duration
            )
            self.db.add(ts_snippet)
            transcript.append(ts_snippet)

        self.db.commit()
        return transcript
