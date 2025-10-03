import re
import regex

def validate_dictionary_entry_json(parsed: dict) -> None:
    """
    Validates the structure and content of the parsed dictionary entry JSON.
    Raises ValueError if something is invalid.
    """

    # Must contain required top-level fields
    required_keys = {"word", "romanized", "translations", "parts_of_speech"}
    if not required_keys.issubset(parsed.keys()):
        missing = required_keys - parsed.keys()
        raise ValueError(f"Missing required keys: {missing}")

    # Validate "word"
    if not isinstance(parsed["word"], str):
        raise ValueError("'word' must be a string")

    # Validate "romanized"
    romanized = parsed["romanized"]
    if not isinstance(romanized, str):
        raise ValueError("'romanized' must be a string")

    latin_regex = regex.compile(r"^[\p{Latin}0-9\s\-\']*$")  # letters, numbers, spaces, hyphen, apostrophe

    # If romanized is present, it must be strictly Latin
    if romanized and not latin_regex.match(romanized):
        raise ValueError(f"'romanized' contains non-Latin characters: {romanized}")

    # Validate "translations"
    translations = parsed["translations"]
    if not isinstance(translations, list):
        raise ValueError("'translations' must be a list")

    if len(translations) < 3:
        raise ValueError("'translations' must contain at least 3 items")

    for i, translation in enumerate(translations, start=0):
        if not isinstance(translation, str):
            raise ValueError(f"translations[{i}] must be a string")

    # Validate "parts_of_speech"
    parts_of_speech = parsed["parts_of_speech"]
    if not isinstance(parts_of_speech, list):
        raise ValueError("'parts_of_speech' must be a list")

    if not parts_of_speech:
        raise ValueError("'parts_of_speech' must contain at least one entry")

    required_pos_keys = {"part_of_speech", "definition", "example", "example_translation"}
    for idx, pos in enumerate(parts_of_speech, start=0):
        if not isinstance(pos, dict):
            raise ValueError(f"parts_of_speech[{idx}] must be a dict")

        missing = required_pos_keys - pos.keys()
        if missing:
            raise ValueError(f"parts_of_speech[{idx}] missing keys: {missing}")

        for key in required_pos_keys:
            if not isinstance(pos[key], str):
                raise ValueError(f"parts_of_speech[{idx}]['{key}'] must be a string")

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
        for key in ("word", "part_of_speech", "romanized", "translations"):
            if key not in part:
                raise ValueError(f"word_parts[{i}] is missing key '{key}'")

        if not isinstance(part["word"], str):
            raise ValueError(f"word_parts[{i}]['word'] must be a string")

        if not isinstance(part["part_of_speech"], str):
            raise ValueError(f"word_parts[{i}]['part_of_speech'] must be a string")

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
            if not isinstance(t, str):
                raise ValueError(
                    f"word_parts[{i}]['translations'][{j}] must be a string"
                )