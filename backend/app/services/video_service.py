from app.stores import VideoStore, LanguageStore, SnippetStore, TranscriptSnippetStore
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig
from models import Video
from dotenv import load_dotenv
import os
import httpx
import asyncio
import json

load_dotenv()

class VideoService:
    def __init__(self, db):
        proxy_username = os.getenv("PROXY_USERNAME")
        proxy_password = os.getenv("PROXY_PASSWORD")

        self.db = db
        self.video_store = VideoStore(db)
        self.snippet_store = SnippetStore(db)
        self.transcript_snippet_store = TranscriptSnippetStore(db)
        self.language_store = LanguageStore(db)
        self.ytt_api = YouTubeTranscriptApi()
        # self.ytt_api = YouTubeTranscriptApi(
        #     proxy_config=GenericProxyConfig(
        #         http_url=f"http://{proxy_username}:{proxy_password}@p.webshare.io:80",
        #         https_url=f"http://{proxy_username}:{proxy_password}@p.webshare.io:80",
        #     )
        # )
        self.google_api_key = os.getenv("GOOGLE_YT_DATA_API_KEY")
        self.ytt_api_url = "https://www.googleapis.com/youtube/v3/videos"
    
    async def fetch_video(self, source_id: str) -> Video:
        try:
            ytt_api_params = {
                "part": "snippet,contentDetails",
                "id": source_id,
                "key": self.google_api_key
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(self.ytt_api_url, params=ytt_api_params)
            
            if response.status_code != 200:
                raise RuntimeError("YouTube API error")

            data = response.json()

            if not data.get("items"):
                raise RuntimeError("Video not found")
            
            title = data["items"][0]["snippet"]["title"]

            video_id = await self.video_store.save_video({
                "source_id": source_id,
                "title": title
            })
            video = await self.video_store.get_video_by_id(video_id, eager_load=True)

            return video
        except Exception as e:
            raise RuntimeError(f"Error occurred while attempting to fetch YouTube video info. {e}")
    
    async def get_video_data(self, source_id: str):
        video = await self.video_store.get_video_by_source_id(source_id, eager_load=True)
        if video:
            return self.get_normalized_video_data(video)

        video = await self.fetch_video(source_id)
        return self.get_normalized_video_data(video)

    def get_normalized_video_data(self, video: Video):
        return {
            "source_id": video.source_id,
            "title": video.title
        }

    async def fetch_transcript_snippets(self, video: Video):
        # Check transcript in DB
        transcript_snippets = await self.transcript_snippet_store.get_ts_snippets_by_video_id(video.id, eager_load=True)
        if transcript_snippets:
            return transcript_snippets

        # Fetch from external API if not in DB
        transcript_data = await self.fetch_ytt_with_retry(video.source_id)

        # Ensure language exists in DB
        language_id = await self.language_store.save_language({
            "code": transcript_data.language_code, 
            "name": transcript_data.language
        })

        await self.video_store.update_video(video, {"language_id": language_id})

        new_snippet_texts = [item.text for item in transcript_data]
        added_snippets = await self.snippet_store.add_snippets(new_snippet_texts, language_id)
        await self.transcript_snippet_store.add_ts_snippets(video.id, added_snippets, transcript_data)
        await self.db.commit()

        return await self.transcript_snippet_store.get_ts_snippets_by_video_id(video.id, eager_load=True)

    async def fetch_ytt_with_retry(self, source_id: str, retries: int = 5):
        for attempt in range(retries):
            try:
                transcript_list = self.ytt_api.list(source_id)
                transcript = next(iter(transcript_list))
                return transcript.fetch()
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(1)
                else:
                    raise RuntimeError(f"Failed to fetch transcript after {retries} attempts. Last error: {e}")