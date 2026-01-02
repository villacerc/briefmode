from models import AIPromptType

class AIPromptService:
    def get_prompt(self, prompt_type: AIPromptType, params: dict) -> str:
        match prompt_type:
            case AIPromptType.SNIPPET_TRANSLATION:
                return self.generate_ai_snippet_translation_prompt(params)
            case AIPromptType.DICTIONARY_POS:
                return self.generate_ai_dictionary_pos_prompt(params)
            case AIPromptType.DICTIONARY_ENTRY:
                return self.generate_ai_dictionary_entry_prompt(params)
            case AIPromptType.TEXT_INTERPRETATION:
                return self.generate_ai_text_interpretation_prompt(params)
            case _:
                raise ValueError(f"Unsupported prompt type: {prompt_type}")

    def generate_ai_dictionary_entry_prompt(self, params: dict) -> str:
        return f"""
                You are a dictionary assistant. 
                Given a word, a source language, and a target language, produce a JSON response according to the rules below.

                Rules
                1. Romanization output: romanized form of the input word in the Latin script.
                2. Translations: Provide up to 4 plausible translations into the target language.
                3. Parts of speech: Provide up to 4 unique parts of speech if available. Each must include:
                    • Part of speech (in English)
                    • Definition (in the target language)
                    • Example sentence in the source language’s native script
                {{
                "word": "<original input word>",
                "romanized": "<romanized form of input word>",
                "phonetic_spelling": "<simplified pronunciation using familiar English letters and stress marks (e.g., huh-LOH, HEE-loh, sah-lahm), avoiding IPA symbols>"
                "translations": "<a list of at least three translation candidates if possible>",
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
                Translate the input below to {params["target_lang_name"]}.
                Rules:
                1. Respond ONLY with valid JSON. Do NOT include explanations, comments, or extra text.
                2. Capitalize the first word only if required by grammar.
                3. Break down input into individual word tokens, including:
                    - "word": original word with punctuation intact. 
                    - "part_of_speech": only include the **main POS label** (e.g., "verb"), not long explanations.
                    - "romanized": Latin script romanization
                    - "translations": at least three translation candidates if possible.
                4. "romanized" must never contain non-Latin characters.
                5. Use properly formatted JSON, double quotes, no trailing commas.

                Output JSON format:

                {{
                    "snippet_text": "<original input text>",
                    "translation": "<full translated sentence here otherwise original text if already in target language>",
                    "word_parts": [
                    {{
                        "word": "<original word with punctuation intact>",
                        "part_of_speech": "<part of speech>",
                        "romanized": "<romanized form in Latin>",
                        "phonetic_spelling": "<simplified pronunciation using familiar English letters and stress marks (e.g., huh-LOH, HEE-loh, sah-lahm), avoiding IPA symbols>",
                        "translations": "<a list of at least three translation candidates if possible in {params["target_lang_name"]}>"
                    }}
                    ]
                }}

                Input:
                {params["text"]}
                """

    def generate_ai_dictionary_pos_prompt(self, params: dict) -> str:
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
