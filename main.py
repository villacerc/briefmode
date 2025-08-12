from youtube_transcript_api import YouTubeTranscriptApi
import asyncio

def main():
    ytt_api = YouTubeTranscriptApi()
    transcript = ytt_api.fetch("oLIkRpKLH1Y")
    print(transcript)

if __name__ == "__main__":
    main()