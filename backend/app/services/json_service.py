import re
import regex
from app.utils.helpers import is_latin_script
from models import AIPromptType

class JSONService():
    def get_validator_callback(self, prompt_type):
        match prompt_type:
            case AIPromptType.DICTIONARY_ENTRY:
                return self.validate_dictionary_entry_json
            case AIPromptType.DICTIONARY_POS:
                return self.validate_dictionary_pos_json
            case AIPromptType.TEXT_INTERPRETATION:
                return self.validate_interpretation_json
            case AIPromptType.SNIPPET_TRANSLATION:
                return self.validate_translation_json
            case AIPromptType.SNIPPET_WORDS_TRANSLATION:
                return self.validate_snippet_words_translation_json
            case _:
                raise ValueError(f"Unsupported prompt type for json validation: {prompt_type}")
  
    def validate_dictionary_pos_json(self, data: dict) -> None:
        """
        Validates the structure and content of the data part-of-speech entry JSON.
        Raises ValueError if something is invalid.
        """
        required_keys = {"parts_of_speech"}
        if not required_keys.issubset(data.keys()):
            raise ValueError(f"Missing required keys: parts_of_speech")

        parts_of_speech = data["parts_of_speech"]
        if not isinstance(parts_of_speech, list):
            raise ValueError("'parts_of_speech' must be a list")

        if not parts_of_speech:
            raise ValueError("'parts_of_speech' must contain at least one entry")

        required_pos_keys = {"part_of_speech", "definition", "example"}
        for idx, pos in enumerate(parts_of_speech, start=0):
            if not isinstance(pos, dict):
                raise ValueError(f"parts_of_speech[{idx}] must be a dict")

            missing = required_pos_keys - pos.keys()
            if missing:
                raise ValueError(f"parts_of_speech[{idx}] missing keys: {missing}")

            for key in required_pos_keys:
                if not isinstance(pos[key], str):
                    raise ValueError(f"parts_of_speech[{idx}]['{key}'] must be a string")

    def validate_dictionary_entry_json(self, data: dict) -> None:
        """
        Validates the structure and content of the data dictionary entry JSON.
        Raises ValueError if something is invalid.
        """

        # Must contain required top-level fields
        required_keys = {"word", "romanized", "translations", "parts_of_speech"}
        if not required_keys.issubset(data.keys()):
            missing = required_keys - data.keys()
            raise ValueError(f"Missing required keys: {missing}")

        # Validate "word"
        if not isinstance(data["word"], str):
            raise ValueError("'word' must be a string")

        # Validate "romanized"
        romanized = data["romanized"]
        if not isinstance(romanized, str):
            raise ValueError("'romanized' must be a string")
            
        # If romanized is present, it must be strictly Latin
        if romanized and not is_latin_script(romanized):
            raise ValueError(f"'romanized' contains non-Latin characters: {romanized}")

        # Validate "translations"
        translations = data["translations"]
        if not isinstance(translations, list):
            raise ValueError("'translations' must be a list")

        if len(translations) < 3:
            raise ValueError("'translations' must contain at least 3 items")

        for i, translation in enumerate(translations, start=0):
            if not isinstance(translation, str):
                raise ValueError(f"translations[{i}] must be a string")

        # Validate "parts_of_speech"
        self.validate_dictionary_pos_json(data)

    def validate_interpretation_json(self, data: dict) -> None:
        """
        Validates the structure and content of the data interpretation JSON.
        Raises ValueError if something is invalid.
        """

        # Must contain required top-level fields
        required_keys = {"is_interpretable", "is_word", "language_code", "normalized_text"}
        if not required_keys.issubset(data.keys()):
            raise ValueError(f"Missing required keys: {required_keys - data.keys()}")

        if not isinstance(data["is_interpretable"], bool):
            raise ValueError("'is_interpretable' must be a boolean")

        if not isinstance(data["is_word"], bool):
            raise ValueError("'is_word' must be a boolean")

        if data["language_code"] is not None and not isinstance(data["language_code"], str):
            raise ValueError("'language_code' must be a string or null")

        if data["normalized_text"] is None or not isinstance(data["normalized_text"], str):
            raise ValueError("'normalized_text' must be a string")

        if data["is_interpretable"]:
            if data["language_code"] is None:
                raise ValueError("'language_code' cannot be null when 'is_interpretable' is true")
            if not data["normalized_text"].strip():
                raise ValueError("'normalized_text' cannot be empty when 'is_interpretable' is true")

    def validate_translation_json(self, data: dict) -> None:
        """
        Validates the structure and content of the data translation JSON.
        Raises ValueError if something is invalid.
        """

        # Must contain required top-level fields
        if "translation" not in data or "word_parts" not in data:
            raise ValueError("Missing required keys: 'translation' and/or 'word_parts'")

        if not isinstance(data["translation"], str):
            raise ValueError("'translation' must be a string")

        if not isinstance(data["word_parts"], list):
            raise ValueError("'word_parts' must be a list")

        for i, part in enumerate(data["word_parts"], start=1):
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

            if part["word"] not in data["snippet_text"]:
                raise ValueError(f"word_parts[{i}]['word'] '{part['word']}' not found in snippet text")

            romanized = part["romanized"]
            if not isinstance(romanized, str):
                raise ValueError(f"word_parts[{i}]['romanized'] must be a string")

            # Check romanized: must be empty or strictly Latin script
            if romanized and not is_latin_script(romanized):
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

    def validate_snippet_words_translation_json(self, data: dict) -> None:
        """
        Validates the structure and content of the translation prompt JSON.
        Raises ValueError if something is invalid.
        """

        # Required top-level keys
        required_keys = ("snippet_text", "translation", "word_parts")
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key: '{key}'")

        if not isinstance(data["snippet_text"], str):
            raise ValueError("'snippet_text' must be a string")

        if not isinstance(data["translation"], str):
            raise ValueError("'translation' must be a string")

        if not isinstance(data["word_parts"], list):
            raise ValueError("'word_parts' must be a list")

        for i, part in enumerate(data["word_parts"], start=1):
            if not isinstance(part, dict):
                raise ValueError(f"word_parts[{i}] must be an object")

            # Required keys per word part
            for key in ("word", "translations"):
                if key not in part:
                    raise ValueError(f"word_parts[{i}] is missing key '{key}'")

            # Validate word
            if not isinstance(part["word"], str):
                raise ValueError(f"word_parts[{i}]['word'] must be a string")

            # Validate translations
            translations = part["translations"]
            if not isinstance(translations, list):
                raise ValueError(f"word_parts[{i}]['translations'] must be a list")

            for j, t in enumerate(translations, start=1):
                if not isinstance(t, str):
                    raise ValueError(
                        f"word_parts[{i}]['translations'][{j}] must be a string"
                    )
