from models import Language
from app.stores import WordStore
from google.oauth2 import service_account
import google.auth.transport.requests
import aiohttp
import os

class TTSService:
    def __init__(self, db):
        self.word_store = WordStore(db)
        self.credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
        self.google_tts_url = "https://texttospeech.googleapis.com/v1beta1/text:synthesize"

    async def get_word_tts_audio(self, word_id: int) -> str:
        try:
            # check if TTS audio already exists in DB
            word = await self.word_store.get_word_by_id(word_id, eager_load=True)
            if not word:
                raise ValueError(f"Word with id {word_id} not found")
            if word.tts_audio:
                return word.tts_audio

            access_token = self.get_google_access_token()
            
            # prepare request payload
            payload = {
                "audioConfig": {
                    "audioEncoding": "mp3",
                    "pitch": 0,
                    "speakingRate": 1
                },
                "input": {
                    "prompt": "Read aloud just the text once in a warm, welcoming tone.",
                    "text": word.text
                },
                "voice": {
                    "languageCode": word.language.bcp47_code,
                    "modelName": "gemini-2.5-flash-lite-preview-tts",
                    "name": "Achernar"
                }
            }

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            # call TTS API
            async with aiohttp.ClientSession() as session:
                async with session.post(self.google_tts_url, json=payload, headers=headers) as resp:
                    data = await resp.json()

            audio_content = data.get("audioContent")

            # save TTS audio to DB
            await self.word_store.update_word(word, {"tts_audio": audio_content})

            return word.tts_audio
        except Exception as e:
            raise RuntimeError(f"Error occurred while attempting to fetch text to speech audio. {e}")
    
    def get_google_access_token(self) -> str:
        try:
            # load service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            # obtain an access token
            auth_req = google.auth.transport.requests.Request()
            credentials.refresh(auth_req)
            return credentials.token
        except Exception as e:
            raise RuntimeError(f"Error occurred while obtaining Google access token. {e}")