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
                return self.generate_ai_text_interpretation_prompt()
            case AIPromptType.SNIPPET_WORDS_TRANSLATION:
                return self.generate_ai_snippet_words_translation_prompt(params)
            case _:
                raise ValueError(f"Unsupported prompt type: {prompt_type}")

    def generate_ai_word_dictionary_prompt(self, params: dict) -> str:
        source_lang_name = params["source_lang_name"]
        target_lang_name = params["target_lang_name"]
        return f"""
            You are a dictionary assistant.

            Analyze the provided word from {source_lang_name} and provide
            language-learning information in {target_lang_name}.

            The input contains:

            * `text`: the text of the word

            Rules:

            1. Preserve `word` exactly as provided.
            2. Provide the standard romanized form of the word using Latin characters.
            3. Provide a simplified English pronunciation using familiar English letters
            and stress marks. Do not use IPA symbols.
            4. Provide up to 4 plausible translations in {target_lang_name}.
            5. Provide up to 4 unique parts of speech when applicable.
            6. For each part of speech:
            - `part_of_speech` must be written in English.
            - `definition` must be written in {target_lang_name}.
            - `example` must be a natural example sentence in
                {source_lang_name}'s native script.
            7. Base translations and definitions on the most common and useful meanings
            of the word.
            8. Do not invent meanings or parts of speech that are not applicable.
            9. Return only the JSON structure defined by the provided schema.
        """
                
    def generate_ai_snippet_translation_prompt(self, params: dict) -> str:
        target_lang_name = params["target_lang_name"]
        return f"""
            Translate the following transcript snippet into {target_lang_name} and provide a word-level language-learning analysis.

            The input contains:

            * `snippet_id`: the unique identifier of the snippet
            * `text`: the original transcript text

            Rules:

            1. Preserve `snippet_id` exactly.
            2. Set `snippet_text` to the original `text` exactly as provided. Do not modify, correct, normalize, or translate it.
            3. Translate the entire snippet into {target_lang_name}.

            * Translate only the text contained in this snippet.
            * The snippet may begin or end in the middle of a sentence. Do not add missing context.
            * If the snippet is already in {target_lang_name}, keep the translation identical to the original text.
            4. Populate `word_parts` with individual words or meaningful expressions useful for language learning.

            * Each `word` must appear in the original `snippet_text`.
            * Include useful grammatical words such as particles.
            * Do not invent words or expressions.
            5. For each `word_parts` entry:

            * `word`: original word or expression exactly as it appears.
            * `part_of_speech`: primary grammatical category.
            * `romanized`: Latin-script romanization using the standard system for the source language.
            * `phonetic_spelling`: simplified English pronunciation guide. Do not use IPA.
            * `translations`: up to three {target_lang_name} meanings appropriate to the context.
            6. `romanized` must contain Latin characters only.
            7. Return only the JSON structure defined by the provided schema. Do not provide explanations or additional fields.
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
    
    def generate_ai_text_interpretation_prompt(self) -> str:
        return f"""
            You are a dictionary assistant.
            Given a string input, determine whether it can be interpreted as belonging to a natural language and whether it represents a word or a phrase. 
            Then produce a JSON response following the rules below.

            The input contains:
    
            * `text`: the text to be interpreted

            Rules:
                1. If the input is in a valid script or a recognizable romanized form, mark it as interpretable.
                2. In languages that do not use spaces (Japanese, Chinese, Korean), treat a single contiguous block of characters as one word if it can stand alone semantically.
                3. Return the ISO 639-1 language code for the detected language when interpretable.
                4. If the input appears to be a partial word or misspelled form, provide the corrected or normalized version in the "normalized_text" field using the same canonical script of the detected language.
                5. If rule #4 does not apply, return the original input unchanged in the "normalized_text" field.
        """
    
    def generate_ai_snippet_words_translation_prompt(self, params: dict) -> str:
        target_lang_name = params["target_lang_name"]
        return f"""
            Translate the following transcript snippet into {target_lang_name} and provide a word-level language-learning analysis.

            The input contains:

            * `snippet_id`: the unique identifier of the snippet
            * `snippet_text`: the original transcript text
            * `snippet_words`: the pre-segmented words in the snippet, each containing `word_id` and `text`

            Rules:

            1. Preserve `snippet_id` exactly.
            2. Translate `snippet_text` into {target_lang_name}.
            3. Use the provided `snippet_words` exactly as the source for word-level analysis.

            * Do not split, combine, add, remove, or reorder the provided words.
            * Preserve every `word_id` exactly.
            * Every provided word must have a corresponding `word_parts` entry.
            4. For each `word_parts` entry:

            * Preserve the corresponding `word_id`.
            * Provide up to three `{target_lang_name}` translations appropriate to the word's context.
            * Use the surrounding snippet context to determine the most appropriate meanings.
            5. Translate only the text contained in this snippet.

            * The snippet may begin or end in the middle of a sentence. Do not add missing context.
            * If the snippet is already in {target_lang_name}, keep the translation identical to the original text.
            6. Return only the JSON structure defined by the provided schema. Do not provide explanations or additional fields.
        """