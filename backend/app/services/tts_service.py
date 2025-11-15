from google.oauth2 import service_account
import google.auth.transport.requests
import aiohttp
import os

class TTSService:
    def __init__(self):
        self.credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH")
        self.google_tts_url = "https://texttospeech.googleapis.com/v1beta1/text:synthesize"

    async def get_tts_audio(self, text: str, lang_bcp47_code: str) -> str:
        try:
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
                    "text": text
                },
                "voice": {
                    "languageCode": lang_bcp47_code,
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

            return data["audioContent"]
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