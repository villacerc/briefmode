from youtube_transcript_api import YouTubeTranscriptApi
import asyncio
from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

def main():
    # ytt_api = YouTubeTranscriptApi()
    # transcript = ytt_api.fetch("oLIkRpKLH1Y")
    # print(transcript)
    load_dotenv()

    AI_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    # client = InferenceClient(token=AI_API_KEY)

    # completion = client.chat.completions.create(
    #     model="deepseek-ai/DeepSeek-R1",
    #     messages=[
    #         {
    #             "role": "user",
    #             "content": "You're an enthusiastic tech blogger who likes to use emojis. Write a short blog about React"
    #         }
    #     ],
    # )

    # print(completion.choices[0].message)

    youtube = build("youtube", "v3", developerKey=GOOGLE_API_KEY)

    request = youtube.search().list(
        part="snippet",
        q="financial education",   # <-- keyword(s)
        type="video",               # Only videos (no channels/playlists)
        maxResults=10,              # Max per request (max 50)
        order="relevance"           # Can be date, rating, viewCount, etc.
    )

    response = request.execute()
    for item in response.get("items", []):
        print(f"Item: {item}")


if __name__ == "__main__":
    main()