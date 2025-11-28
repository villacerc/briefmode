from app.stores import VideoStore, LanguageStore
from youtube_transcript_api import YouTubeTranscriptApi
from models import Video
import os
import httpx

class VideoService:
    def __init__(self, db):
        self.video_store = VideoStore(db)
        self.language_store = LanguageStore(db)
        self.ytt_api = YouTubeTranscriptApi()
        self.google_api_key = os.getenv("GOOGLE_YT_DATA_API_KEY")
        self.ytt_api_url = "https://www.googleapis.com/youtube/v3/videos"
    
    async def fetch_video_info(self, source_id: str) -> Video:
        try:
            video = self.video_store.get_video_by_source_id(source_id)
            if video:
                return self.get_normalized_video_info(video)

            params = {
                "part": "snippet,contentDetails",
                "id": source_id,
                "key": self.google_api_key
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(self.ytt_api_url, params=params)
            
            if response.status_code != 200:
                raise RuntimeError("YouTube API error")

            data = response.json()

            if not data.get("items"):
                raise RuntimeError("Video not found")
            
            language_code = data["items"][0]["snippet"].get("defaultAudioLanguage", "en")
            language = self.language_store.get_by_code(language_code)
            title = data["items"][0]["snippet"]["title"]

            video = self.video_store.save_video({
                "source_id": source_id,
                "title": title,
                "language_id": language.id
            })

            return self.get_normalized_video_info(video)
        except Exception as e:
            raise RuntimeError(f"Error occurred while attempting to fetch YouTube video info. {e}")

    def get_normalized_video_info(self, video: Video):
        return {
            "source_id": video.source_id,
            "title": video.title,
            "source_lang_code": video.language.code
        }
        
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
        self.video_store.save_transcript_snippets(source_id, language, transcript_data)
        return self.video_store.get_transcript_snippets(source_id)
