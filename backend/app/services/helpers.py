import re

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

    latin_regex = re.compile(r"^[A-Za-z0-9\s\-\']*$")  # allow letters, numbers, spaces, hyphen, apostrophe

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

    # 5. Strip accents if for search
    word = ''.join(
        c for c in unicodedata.normalize('NFD', word)
        if unicodedata.category(c) != 'Mn'
    )

    return word