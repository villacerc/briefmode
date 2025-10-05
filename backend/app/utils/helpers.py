import re
import regex
import unicodedata
import asyncio
import random
import unicodedata
from openai import AsyncOpenAI
import os
import json

NO_SPACE_LANGUAGES = ["ja", "zh", "th", "lo", "km", "my", "bo", "mn"]
GPT_MODEL = "gpt-4.1-nano"

async def fetch_ai_data(prompt: str, validate_fetched_ai_json: callable) -> dict:
    async_openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    parsed_json = None
    max_retries = 3
    for attempt in range(max_retries):
        response = await retry_with_backoff(
            async_openai_client.responses.create(
                model=GPT_MODEL,
                input=prompt,
                store=False
            )
        )

        raw_text = response.output[0].content[0].text.strip()
        try:
            parsed_json = json.loads(raw_text)
            validate_fetched_ai_json(parsed_json)
            return parsed_json
        except (json.JSONDecodeError, ValueError) as e:
            print(
                f"Attempt {attempt + 1}/{max_retries} failed: {type(e).__name__} - {e}. Retrying..."
            )
            if attempt == max_retries - 1:
                raise RuntimeError(f"Failed to fetch AI data after {max_retries} attempts. Last error: {e}") from e
            await asyncio.sleep(1)

def is_latin_script(text: str) -> bool:
    """Return True if all alphabetic characters are from the Latin script."""
    for ch in text:
        if ch.isalpha():
            try:
                if "LATIN" not in unicodedata.name(ch):
                    return False
            except ValueError:
                # Character has no Unicode name
                return False
    return True

def sanitize_word(word: str) -> str:
    # 1. Unicode normalize
    word = unicodedata.normalize("NFC", word)

    # 2. Casefold (Unicode-aware lowercase)
    word = word.casefold()

    # 3. Remove ASCII punctuation except apostrophe
    word = re.sub(r"[!¡¿\"#$%&()*+,\-./:;<=>?@[\\\]^_`{|}~]", "", word)

    # 4. Collapse whitespace
    word = re.sub(r"\s+", " ", word).strip()

    # 5. Strip accents
    word = ''.join(
        c for c in unicodedata.normalize('NFD', word)
        if unicodedata.category(c) != 'Mn'
    )

    return word

def sanitize_phrase(phrase: str, lang: str = "en") -> str:
    # Unicode normalize + casefold
    phrase = unicodedata.normalize("NFC", phrase)
    phrase = phrase.casefold()

    # Remove punctuation except apostrophe
    phrase = re.sub(r"[!\"#$%&()*+,-./:;<=>?@[\\\]^_`{|}~]", "", phrase)

    # If language uses spaces, sanitize each word separately
    if lang not in NO_SPACE_LANGUAGES:
        words = phrase.split()
        words = [sanitize_word(w) for w in words if w]
        phrase = " ".join(words)
    else:
        # For no-space languages, sanitize the string as a whole
        phrase = sanitize_word(phrase)

    return phrase

async def retry_with_backoff(coro, retries=5, base_delay=1):
    for attempt in range(retries):
        try:
            return await coro
        except Exception as e:
            if attempt == retries - 1:
                raise RuntimeError(f"Operation failed after {retries} attempts. {str(e)}") from e
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
            await asyncio.sleep(delay)