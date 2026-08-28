from models import AIPromptType

class AIPromptService:
    def get_prompt(self, prompt_type: AIPromptType, params: dict) -> str:
        match prompt_type:
            case AIPromptType.SNIPPET_TRANSLATION:
                return self.generate_ai_snippet_translation_prompt(params)
            case AIPromptType.WORD_POS:
                return self.generate_ai_word_pos_prompt(params)
            case AIPromptType.WORD_DICTIONARY:
                return self.generate_ai_word_dictionary_prompt(params)
            case AIPromptType.TEXT_INTERPRETATION:
                return self.generate_ai_text_interpretation_prompt(params)
            case AIPromptType.SNIPPET_WORDS_TRANSLATION:
                return self.generate_ai_snippet_words_translation_prompt(params)
            case _:
                raise ValueError(f"Unsupported prompt type: {prompt_type}")

    def generate_ai_word_dictionary_prompt(self, params: dict) -> str:
        return f"""
                You are a dictionary assistant. 
                Given a word, a source language, and a target language, produce a JSON response according to the rules below.

                Rules
                1. Romanization output: romanized form of the input word in the Latin script.
                2. Translations: Provide a list of up to 4 plausible translations into the target language.
                3. Parts of speech: Provide up to 4 unique parts of speech if available. Each must include:
                    • Part of speech (in English)
                    • Definition (in the target language)
                    • Example sentence in the source language’s native script
                {{
                    "word": "<original input word>",
                    "romanized": "<romanized form of input word>",
                    "phonetic_spelling": "<simplified pronunciation using familiar English letters and stress marks (e.g., huh-LOH, HEE-loh, sah-lahm), avoiding IPA symbols>"
                    "translations": [
                        "<candidate 1>",
                        "<candidate 2>",
                        "<candidate 3>"
                    ],
                    "parts_of_speech": [
                            {{
                                "part_of_speech": "<part of speech in english>",
                                "definition": "<definition of the word in the **target** language>",
                                "example": "<example sentence in the source language's script>",
                            }}
                        ]
                }}

                Input word: {params["text"]}
                Source language: {params["source_lang_name"]}
                Target language: {params["target_lang_name"]}
                """
                
    def generate_ai_snippet_translation_prompt(self, params: dict) -> str:
        return f"""
               Translate the following transcript snippets into {params["target_lang_name"]}.

                The input is a JSON array of transcript snippets.

                Rules:
                1. Respond ONLY with valid JSON. Do NOT include explanations, markdown, comments, or extra text.
                2. Return a JSON array.
                3. The output array MUST contain EXACTLY the same number of objects as the input array.
                4. Preserve the input order exactly.
                5. Each output object MUST contain the same "id" as its corresponding input object.
                6. Do NOT merge, split, reorder, or omit snippets.
                7. Transcript snippets may begin or end in the middle of a sentence. Translate EACH snippet independently exactly as provided. Do NOT combine adjacent snippets into complete sentences.
                8. If a snippet is already in {params["target_lang_name"]}, keep its translation identical to the original text.
                9. Capitalize the first word only if required by grammar.
                10. Break each snippet into individual word tokens:
                    - "word": original word with punctuation intact.
                    - "part_of_speech": only the main POS label (e.g. "verb").
                    - "romanized": Latin script only.
                    - "phonetic_spelling": simplified English pronunciation (not IPA).
                    - "translations": at least three translation candidates when possible.
                11. "romanized" must never contain non-Latin characters.
                12. Return properly formatted JSON using double quotes and no trailing commas.

                Output format:
                [
                    {{
                        "snippet_id": <same input id>,
                        "snippet_text": "<original input text>",
                        "translation": "<translated snippet>",
                        "word_parts": [
                            {{
                                "word": "<original word>",
                                "part_of_speech": "<part of speech>",
                                "romanized": "<romanized form>",
                                "phonetic_spelling": "<simplified pronunciation>",
                                "translations": [
                                    "<candidate 1>",
                                    "<candidate 2>",
                                    "<candidate 3>"
                                ]
                            }}
                        ]
                    }}
                ]

                Input:

                {params["snippets"]}
                """

    def generate_ai_word_pos_prompt(self, params: dict) -> str:
        return f"""
                You are a dictionary assistant. 
                Given a word, a source language, and a target language, produce a JSON response according to the rules below.

                Rules
                1. Parts of speech: Provide up to 4 unique parts of speech of the input word if available. Each must include:
                    • Part of speech (in English)
                    • Definition (in the target language)
                    • Example sentence in the source language’s native script
                {{

                "parts_of_speech": [
                        {{
                            "part_of_speech": "<part of speech in english>",
                            "definition": "<definition of the word in the **target** language>",
                            "example": "<example sentence in the source language's script>",
                        }}
                    ]
                }}

                Input word: {params["text"]}
                Source language: {params["source_lang_name"]}
                Target language: {params["target_lang_name"]}
                """
    
    def generate_ai_text_interpretation_prompt(self, params: dict) -> str:
        return f"""
                You are a dictionary assistant.
                Given a string input, determine whether it can be interpreted as belonging to a natural language and whether it represents a word or a phrase. 
                Then produce a JSON response following the rules below.

                Rules:
                    1. If the input is in a valid script or a recognizable romanized form, mark it as interpretable.
                    2. In languages that do not use spaces (Japanese, Chinese, Korean), treat a single contiguous block of characters as one word if it can stand alone semantically.
                    3. Return the ISO 639-1 language code for the detected language when interpretable.
                    4. If the input appears to be a partial word or misspelled form, provide the corrected or normalized version in the "normalized_text" field using the same canonical script of the detected language.
                    5. If rule #4 does not apply, return the original input unchanged in the "normalized_text" field.

                {{
                    "is_interpretable": true | false,
                    "is_word": true | false,
                    "language_code": "xx" | null,
                    "normalized_text": "string"
                }}

                Input: {params["text"]}
                """
    
    def generate_ai_snippet_words_translation_prompt(self, params: dict) -> str:
        return f"""
                Translate the words from the following transcript snippets into
                {params["target_lang_name"]}.

                The input is a JSON array of snippet words.

                Rules:
                1. Respond ONLY with valid JSON. Do NOT include explanations, comments,
                markdown, or extra text.
                2. Return a JSON array.
                3. Return exactly one output object for each snippet id.
                4. Preserve the input order exactly.
                5. Do not add, remove, merge, split, or reorder snippet words.
                6. Each output object must contain:
                - "snippet_id": provided id of the snippet
                - "translation": the translated snippet text
                - "word_parts": list of word objects
                7. Each word_part object must contain
                - "word_id": provided id of the word
                - "translations": list of translation candidates
                8. Provide at least three translation candidates for each word when possible.
                9. If a word has no reasonable translation, return an empty list.
                10. Return properly formatted JSON using double quotes and no trailing commas.

                Output format:
                [
                    {{
                        "snippet_id": <same input snippet id>,
                        "translation": "<translated snippet text>",
                        "word_parts": [
                            {{
                                "word_id": <same input word id>,
                                "translations": [
                                    "<candidate 1>",
                                    "<candidate 2>",
                                    "<candidate 3>"
                                ]
                            }}
                        ]
                    }}
                ]

                Input:
                {params["snippets"]}
                """