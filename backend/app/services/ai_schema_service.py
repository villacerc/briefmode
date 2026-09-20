from models import AIPromptType

class AISchemaService:
    def get_schema(self, prompt_type: AIPromptType) -> dict:
        match prompt_type:
            case AIPromptType.SNIPPET_WORDS_TRANSLATION:
                return self.generate_ai_snippet_words_translation_prompt_schema()
            case AIPromptType.SNIPPET_TRANSLATION:
                return self.generate_ai_snippet_translation_schema()
            case _:
                raise ValueError(f"Unsupported prompt type: {prompt_type}")

    def generate_ai_snippet_words_translation_prompt_schema(self) -> dict:
        return {
            "format": {
                "type": "json_schema",
                    "name": "snippet_word_translations",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                        "snippet_id": {
                            "type": "integer"
                        },
                        "translation": {
                            "type": "string"
                        },
                        "word_parts": {
                            "type": "array",
                            "items": {
                            "type": "object",
                            "properties": {
                                "word_id": {
                                "type": "integer"
                                },
                                "translations": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                                }
                            },
                            "required": [
                                "word_id",
                                "translations"
                            ],
                            "additionalProperties": False
                            }
                        }
                        },
                        "required": [
                        "snippet_id",
                        "translation",
                        "word_parts"
                        ],
                        "additionalProperties": False
                    }
            }
        }

    def generate_ai_snippet_translation_schema(self) -> dict:
      return {
        "format": {
            "type": "json_schema",
            "name": "snippet_translation",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "snippet_id": {
                        "type": "integer"
                    },
                    "snippet_text": {
                        "type": "string"
                    },
                    "translation": {
                        "type": "string"
                    },
                    "word_parts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "word": {
                                    "type": "string"
                                },
                                "part_of_speech": {
                                    "type": "string"
                                },
                                "romanized": {
                                    "type": "string"
                                },
                                "phonetic_spelling": {
                                    "type": "string"
                                },
                                "translations": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                }
                            },
                            "required": [
                                "word",
                                "part_of_speech",
                                "romanized",
                                "phonetic_spelling",
                                "translations"
                            ],
                            "additionalProperties": False
                        }
                    }
                },
                "required": [
                    "snippet_id",
                    "snippet_text",
                    "translation",
                    "word_parts"
                ],
                "additionalProperties": False
            }
        }
    }