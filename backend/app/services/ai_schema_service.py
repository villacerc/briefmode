from models import AIPromptType

class AISchemaService:
    def get_schema(self, prompt_type: AIPromptType) -> dict:
        match prompt_type:
            case AIPromptType.TEXT_INTERPRETATION:
                return self.generate_text_interpretation_prompt_schema()
            case AIPromptType.WORD_DICTIONARY:
                return self.generate_ai_word_dictionary_prompt_schema()
            case AIPromptType.SNIPPET_WORDS_TRANSLATION:
                return self.generate_ai_snippet_words_translation_prompt_schema()
            case AIPromptType.SNIPPET_TRANSLATION:
                return self.generate_ai_snippet_translation_schema()
            case _:
                raise ValueError(f"Unsupported prompt type: {prompt_type}")
            
    def generate_text_interpretation_prompt_schema(self) -> dict:
        return {
            "format": {
                "type": "json_schema",
                "name": "text_interpretation",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "is_interpretable": {
                            "type": "boolean"
                        },
                        "is_word": {
                            "type": "boolean"
                        },
                        "language_code": {
                            "anyOf": [
                                {
                                    "type": "string"
                                },
                                {
                                    "type": "null"
                                }
                            ]
                        },
                        "normalized_text": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "is_interpretable",
                        "is_word",
                        "language_code",
                        "normalized_text"
                    ],
                    "additionalProperties": False
                }
            }
        }
            
    def generate_ai_word_dictionary_prompt_schema(self) -> dict:
        return {
            "format": {
                "type": "json_schema",
                "name": "word_dictionary",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "word": {
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
                        },
                        "parts_of_speech": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "part_of_speech": {
                                        "type": "string"
                                    },
                                    "definition": {
                                        "type": "string"
                                    },
                                    "example": {
                                        "type": "string"
                                    }
                                },
                                "required": [
                                    "part_of_speech",
                                    "definition",
                                    "example"
                                ],
                                "additionalProperties": False
                            }
                        }
                    },
                    "required": [
                        "word",
                        "romanized",
                        "phonetic_spelling",
                        "translations",
                        "parts_of_speech"
                    ],
                    "additionalProperties": False
                }
            }
        }

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