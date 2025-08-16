from urllib import response
from youtube_transcript_api import YouTubeTranscriptApi
import asyncio
from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
import json
from azure.ai.translation.text import TextTranslationClient
from azure.core.credentials import AzureKeyCredential

def main():
    # ytt_api = YouTubeTranscriptApi()
    # transcript = ytt_api.fetch("oLIkRpKLH1Y")
    # print(transcript)
    load_dotenv()

    key = os.getenv("TRANSLATOR_API_KEY")
    endpoint = "https://api.cognitive.microsofttranslator.com/"          # e.g., https://<your-resource>.cognitiveservices.azure.com/
    region = "westus"

    credential = AzureKeyCredential(key)
    text_translator = TextTranslationClient(credential=credential, region=region)
    
    try:
        input_text = ["This is a test.", "hello darkness"]
        response = text_translator.translate(
            body=input_text,
            to_language=["fr"],          # list of target languages
        )
        for idx, translation_result in enumerate(response):
            print(f"Input: {input_text[idx]}")
            for t in translation_result.translations:
                print(f"  Translated to {t.to}: {t.text}")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()