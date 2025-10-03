from app.stores import VideoStore, LanguageStore
from youtube_transcript_api import YouTubeTranscriptApi

class VideoService:
    def __init__(self, db):
        self.video_store = VideoStore(db)
        self.language_store = LanguageStore(db)
        self.ytt_api = YouTubeTranscriptApi()

    def fetch_transcript_snippets(self, source_id: str):
        # Check transcript in DB
        transcript_snippets = self.video_store.get_transcript_snippets(source_id)
        if transcript_snippets:
            return transcript_snippets

        # Fetch from external API if not in DB
        transcript_list = self.ytt_api.list(source_id)
        first_transcript = next(iter(transcript_list))
        transcript_data = self.ytt_api.fetch(source_id, languages=[first_transcript.language_code])

        # Ensure language exists in DB
        language = None
        if not self.language_store.language_exists(transcript_data.language_code):
            language = self.language_store.create(
                code=transcript_data.language_code,
                name=transcript_data.language
            )
        else:
            language = self.language_store.get_by_code(transcript_data.language_code)

        # Persist new video + transcript
        return self.video_store.save_transcript_snippets(source_id, language, transcript_data)
