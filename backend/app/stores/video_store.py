from sqlalchemy import select
from sqlalchemy.orm import joinedload
from models import Video, TranscriptSnippet, Snippet, SnippetWord, Word, Language
from app.services.helpers import sanitize_phrase

class VideoStore:
    def __init__(self, db):
        self.db = db

    def get_video(self, video_id: int):
        return self.db.query(Video).filter(Video.id == video_id).first()

    def get_transcript_snippets(self, source_id: str):
        video = self.db.execute(
            select(Video).options(
                joinedload(Video.transcript_snippets)
                .joinedload(TranscriptSnippet.snippet)
                .joinedload(Snippet.snippet_words)
                .joinedload(SnippetWord.word)
                .joinedload(Word.translations),
                joinedload(Video.transcript_snippets)
                .joinedload(TranscriptSnippet.snippet)
                .joinedload(Snippet.language)
            ).where(Video.source_id == source_id)
        ).scalars().first()

        if video and video.transcript_snippets:
            return video.transcript_snippets
        return None

    def save_transcript_snippets(self, source_id: str, language: Language, transcript_data):
        video = Video(source_id=source_id)
        self.db.add(video)
        self.db.flush()

        transcript_snippets = []
        for i, item in enumerate(transcript_data.snippets):
            sanitized_phrase = sanitize_phrase(item.text, language.code)
            snippet = Snippet(language=language, text=sanitized_phrase)
            self.db.add(snippet)
            self.db.flush()
            
            ts_snippet = TranscriptSnippet(
                video_id=video.id,
                snippet_id=snippet.id,
                text=item.text,
                start=item.start,
                end=transcript_data[i + 1].start if i < len(transcript_data) - 1 else item.start + item.duration,
                duration=item.duration
            )
            self.db.add(ts_snippet)
            transcript_snippets.append(ts_snippet)

        self.db.commit()
        return transcript_snippets
