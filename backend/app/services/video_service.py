from app.stores import VideoStore, LanguageStore
from youtube_transcript_api import YouTubeTranscriptApi

class VideoService:
    def __init__(self, db):
        self.video_store = VideoStore(db)
        self.language_store = LanguageStore(db)
        self.ytt_api = YouTubeTranscriptApi()

    def fetch_transcript(self, source_id: str):
        # Check transcript in DB
        transcript = self.video_store.get_transcript(source_id)
        if transcript:
            return transcript

        # Fetch from external API if not in DB
        transcript_list = self.ytt_api.list(source_id)
        first_transcript = next(iter(transcript_list))
        transcript_data = self.ytt_api.fetch(source_id, languages=[first_transcript.language_code])

        # Ensure language exists in DB
        language = self.language_store.get_by_code(
            code=transcript_data.language_code
        )
        if not language:
            language = self.language_store.create(
                code=transcript_data.language_code,
                name=transcript_data.language
            )

        # Persist new video + transcript
        return self.video_store.save_transcript(source_id, language.id, transcript_data)
