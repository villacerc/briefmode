import re
import regex
import unicodedata

NO_SPACE_LANGUAGES = ["ja", "zh", "th", "lo", "km", "my", "bo", "mn"]
GPT_MODEL = "gpt-4.1-nano"

def validate_interpretation_json(parsed: dict) -> None:
    """
    Validates the structure and content of the parsed interpretation JSON.
    Raises ValueError if something is invalid.
    """

    # Must contain required top-level fields
    required_keys = {"is_interpretable", "is_word", "language_code", "normalized_text"}
    if not required_keys.issubset(parsed.keys()):
        raise ValueError(f"Missing required keys: {required_keys - parsed.keys()}")

    if not isinstance(parsed["is_interpretable"], bool):
        raise ValueError("'is_interpretable' must be a boolean")

    if not isinstance(parsed["is_word"], bool):
        raise ValueError("'is_word' must be a boolean")

    if parsed["language_code"] is not None and not isinstance(parsed["language_code"], str):
        raise ValueError("'language_code' must be a string or null")

    if parsed["normalized_text"] is not None and not isinstance(parsed["normalized_text"], str):
        raise ValueError("'normalized_text' must be a string or null")

def validate_translation_json(parsed: dict, snippet_text: str) -> None:
    """
    Validates the structure and content of the parsed translation JSON.
    Raises ValueError if something is invalid.
    """

    # Must contain required top-level fields
    if "translation" not in parsed or "word_parts" not in parsed:
        raise ValueError("Missing required keys: 'translation' and/or 'word_parts'")

    if not isinstance(parsed["translation"], str):
        raise ValueError("'translation' must be a string")

    if not isinstance(parsed["word_parts"], list):
        raise ValueError("'word_parts' must be a list")

    latin_regex = regex.compile(r"^[\p{Latin}0-9\s\-\']*$")  # allow letters, numbers, spaces, hyphen, apostrophe

    for i, part in enumerate(parsed["word_parts"], start=1):
        if not isinstance(part, dict):
            raise ValueError(f"word_parts[{i}] must be an object")

        # Required keys in each word part
        for key in ("word", "romanized", "translations"):
            if key not in part:
                raise ValueError(f"word_parts[{i}] is missing key '{key}'")

        if not isinstance(part["word"], str):
            raise ValueError(f"word_parts[{i}]['word'] must be a string")
        
        if part["word"] not in snippet_text:
            raise ValueError(f"word_parts[{i}]['word'] '{part['word']}' not found in snippet text")

        romanized = part["romanized"]
        if not isinstance(romanized, str):
            raise ValueError(f"word_parts[{i}]['romanized'] must be a string")

        # Check romanized: must be empty or strictly Latin script
        if romanized and not latin_regex.match(romanized):
            raise ValueError(
                f"word_parts[{i}]['romanized'] contains non-Latin characters: {romanized}"
            )

        # Validate translations list
        translations = part["translations"]
        if not isinstance(translations, list):
            raise ValueError(f"word_parts[{i}]['translations'] must be a list")

        for j, t in enumerate(translations, start=1):
            if not isinstance(t, dict) or "translation" not in t:
                raise ValueError(
                    f"word_parts[{i}]['translations'][{j}] must be an object with key 'translation'"
                )
            if not isinstance(t["translation"], str):
                raise ValueError(
                    f"word_parts[{i}]['translations'][{j}]['translation'] must be a string"
                )

def sanitize_word(word: str) -> str:
    # 1. Unicode normalize
    word = unicodedata.normalize("NFC", word)

    # 2. Casefold (Unicode-aware lowercase)
    word = word.casefold()

    # 3. Remove ASCII punctuation except apostrophe
    word = re.sub(r"[!\"#$%&()*+,-./:;<=>?@[\\\]^_`{|}~]", "", word)

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