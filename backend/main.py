from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from youtube_transcript_api import YouTubeTranscriptApi
import re
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
import uvicorn
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor()

app = FastAPI(
    title="Briefmode",
    description="YouTube Video Blog Posts",
    version="1.0.0"
)

class VideoIDRequest(BaseModel):
    video_id: str

# API Routes
@app.get("/", summary="Health Check")
async def root():
    """
    Internal function to fetch transcript by video ID.
    """
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch('oLIkRpKLH1Y')
        return {
            "message": "Transcript fetched successfully",
            "data": transcript
        }
    except Exception as e:
        print("Full error:", repr(e))
        return {
            "message": "Failed to fetch transcript"
        }
# async def root():
#     """Simple health check endpoint."""
#     return {
#         "message": "YouTube Transcript API is running",
#         "status": "healthy",
#         "version": "1.0.0"
#     }

async def get_transcript_by_id():
    """
    Internal function to fetch transcript by video ID.
    """
    try:
        transcript = YouTubeTranscriptApi.get_transcript('oLIkRpKLH1Y')
        print(transcript)
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, TooManyRequests) as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)