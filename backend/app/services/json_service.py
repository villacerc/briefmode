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

    def validate_translation_json(self, data: list[dict]) -> None:
        if not isinstance(data, list):
            raise ValueError("Response must be a JSON array")

        for i, snippet in enumerate(data):
            if not isinstance(snippet, dict):
                raise ValueError(f"Item {i} must be an object")

            self._validate_translation_object(snippet)

    def _validate_translation_object(self, data: dict) -> None:
        """Validate a translated transcript snippet."""

        self._require_keys(
            data,
            ("snippet_id", "snippet_text", "translation", "word_parts"),
        )

        self._require_type(data["snippet_id"], (int, str), "snippet_id")
        self._require_type(data["snippet_text"], str, "snippet_text")
        self._require_type(data["translation"], str, "translation")
        self._require_type(data["word_parts"], list, "word_parts")

        for i, part in enumerate(data["word_parts"], start=1):
            self._validate_word_part(
                part,
                index=i,
                snippet_text=data["snippet_text"],
            )

    def _validate_word_part(
        self,
        part: dict,
        *,
        index: int,
        snippet_text: str,
    ) -> None:
        if not isinstance(part, dict):
            raise ValueError(f"word_parts[{index}] must be an object")

        self._require_keys(
            part,
            (
                "word",
                "part_of_speech",
                "romanized",
                "phonetic_spelling",
                "translations",
            ),
        )

        self._require_type(part["word"], str, f"word_parts[{index}]['word']")
        self._require_type(
            part["part_of_speech"],
            str,
            f"word_parts[{index}]['part_of_speech']",
        )
        self._require_type(
            part["romanized"],
            str,
            f"word_parts[{index}]['romanized']",
        )
        self._require_type(
            part["phonetic_spelling"],
            str,
            f"word_parts[{index}]['phonetic_spelling']",
        )
        self._require_type(
            part["translations"],
            list,
            f"word_parts[{index}]['translations']",
        )

        if part["word"] not in snippet_text:
            raise ValueError(
                f"word_parts[{index}]['word'] '{part['word']}' "
                "not found in snippet text"
            )

        romanized = part["romanized"]
        if romanized and not is_latin_script(romanized):
            raise ValueError(
                f"word_parts[{index}]['romanized'] contains "
                f"non-Latin characters: {romanized}"
            )

        phonetic = part["phonetic_spelling"]
        if phonetic and not is_latin_script(phonetic):
            raise ValueError(
                f"word_parts[{index}]['phonetic_spelling'] contains "
                f"non-Latin characters: {phonetic}"
            )

        for j, translation in enumerate(part["translations"], start=1):
            self._require_type(
                translation,
                str,
                f"word_parts[{index}]['translations'][{j}]",
            )

    def validate_snippet_words_translation_json(self, data: list) -> None:
        """
        Validates the structure and content of the snippet word translation JSON.
        Raises ValueError if something is invalid.
        """

        self._require_type(data, list, "data")

        for i, snippet in enumerate(data, start=1):
            if not isinstance(snippet, dict):
                raise ValueError(f"data[{i}] must be an object")

            # Required snippet keys
            self._require_keys(
                snippet,
                ("snippet_id", "translation", "word_parts")
            )

            # Validate snippet_id
            if not isinstance(snippet["snippet_id"], (int, str)):
                raise ValueError(
                    f"data[{i}]['snippet_id'] must be an integer or string"
                )

            # Validate translation
            self._require_type(
                snippet["translation"],
                str,
                f"data[{i}]['translation']"
            )

            # Validate word_parts
            self._require_type(
                snippet["word_parts"],
                list,
                f"data[{i}]['word_parts']"
            )

            for j, part in enumerate(snippet["word_parts"], start=1):
                if not isinstance(part, dict):
                    raise ValueError(
                        f"data[{i}]['word_parts'][{j}] must be an object"
                    )

                # Required word part keys
                self._require_keys(
                    part,
                    ("word_id", "translations")
                )

                # Validate word_id
                if not isinstance(part["word_id"], (int, str)):
                    raise ValueError(
                        f"data[{i}]['word_parts'][{j}]['word_id'] "
                        "must be an integer or string"
                    )

                # Validate translations
                translations = part["translations"]

                self._require_type(
                    translations,
                    list,
                    f"data[{i}]['word_parts'][{j}]['translations']"
                )

                for k, translation in enumerate(translations, start=1):
                    self._require_type(
                        translation,
                        str,
                        f"data[{i}]['word_parts'][{j}]['translations'][{k}]"
                    )

    def _require_keys(self, obj: dict, required: tuple[str, ...]) -> None:
        missing = [key for key in required if key not in obj]
        if missing:
            raise ValueError(f"Missing required keys: {', '.join(missing)}")

    def _require_type(self, value, expected_type, field: str) -> None:
        if not isinstance(value, expected_type):
            if isinstance(expected_type, tuple):
                expected = " or ".join(t.__name__ for t in expected_type)
            else:
                expected = expected_type.__name__

            raise ValueError(f"'{field}' must be {expected}")