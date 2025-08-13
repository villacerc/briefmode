from youtube_transcript_api import YouTubeTranscriptApi
import asyncio
from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

def main():
    # ytt_api = YouTubeTranscriptApi()
    # transcript = ytt_api.fetch("oLIkRpKLH1Y")
    # print(transcript)
    load_dotenv()

    API_TOKEN = os.getenv("HUGGINGFACE_API_KEY")

    client = InferenceClient(token=API_TOKEN)

    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1",
        messages=[
            {
                "role": "user",
                "content": "You're an enthusiastic tech blogger who likes to use emojis. Write a short blog about React"
            }
        ],
    )

    print(completion.choices[0].message)

if __name__ == "__main__":
    main()