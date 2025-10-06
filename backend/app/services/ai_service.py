from .json_service import JSONService
from models import Language
from openai import AsyncOpenAI
import os
import json
import asyncio

class AIService:
    def __init__(self):
        self.gpt_model = "gpt-4.1-nano"
        self.async_openai_client = AsyncOpenAI(api_key = os.getenv("OPENAI_API_KEY"))
        self.json_service = JSONService()

    async def fetch_ai_data(self, prompt: str, validate_fetched_ai_json: callable) -> dict:
        parsed_json = None
        max_retries = 3
        for attempt in range(max_retries):
            response = await self.retry_with_backoff(
                self.async_openai_client.responses.create(
                    model=self.gpt_model,
                    input=prompt,
                    store=False
                )
            )

            raw_text = response.output[0].content[0].text.strip()
            try:
                parsed_json = json.loads(raw_text)
                validate_fetched_ai_json(parsed_json)
                return parsed_json
            except (json.JSONDecodeError, ValueError) as e:
                print(
                    f"Attempt {attempt + 1}/{max_retries} failed: {type(e).__name__} - {e}. Retrying..."
                )
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to fetch AI data after {max_retries} attempts. Last error: {e}") from e
                await asyncio.sleep(1)

    async def retry_with_backoff(self, coro, retries=5, base_delay=1):
        for attempt in range(retries):
            try:
                return await coro
            except Exception as e:
                if attempt == retries - 1:
                    raise RuntimeError(f"Operation failed after {retries} attempts. {str(e)}") from e
                delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                await asyncio.sleep(delay)
    
    async def fetch_ai_text_interpretation(self, text: str):
        try:
            prompt = f"""
                    You are a dictionary assistant.
                    Given a string input, determine whether it can be interpreted as belonging to a natural language and whether it represents a word or a phrase. 
                    Then produce a JSON response following the rules below.

                    Rules:
                        1. If the input is in a valid script or a recognizable romanized form, mark it as interpretable.
                        2. Distinguish between a word (single token, no whitespace in space-based languages) and a phrase (multiple tokens or a valid construction in non-space languages).
                        3. Return the ISO 639-1 language code for the detected language when interpretable.
                        4. If the input appears to be a partial word or misspelled form, provide the corrected or normalized version in the "normalized_text" field using the same canonical script of the detected language.

                    {{
                        "is_interpretable": true | false,
                        "is_word": true | false,
                        "language_code": "xx" | null,
                        "normalized_text": "string" | null
                    }}

                    Input: {text}
                    """
            parsed_json = await self.fetch_ai_data(prompt, self.json_service.validate_interpretation_json)
            return parsed_json
        except Exception as e:
            raise RuntimeError(f"Error fetching AI text interpretation for '{text}'. {e}")

    async def fetch_ai_dictionary_entry(self, input: str, source_lang: Language, target_lang: Language):
            try:
                prompt = f"""
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
                        "translations": "<a list of at least three translation candidates if possible>",
                        "parts_of_speech": [
                                {{
                                "part_of_speech": "<part of speech in english>",
                                "definition": "<definition of the word in the **target** language>",
                                "example": "<example sentence in the source language's script>",
                                }}
                            ]
                        }}

                        Input word: {input}
                        Source language: {source_lang.name}
                        Target language: {target_lang.name}
                        """
                parsed_json = await self.fetch_ai_data(prompt, self.json_service.validate_dictionary_entry_json)
                return parsed_json
            except Exception as e:
                raise RuntimeError(f"Error fetching AI dictionary entry for '{input}'. {e}")

    async def fetch_ai_dictionary_pos(self, input: str, source_lang: Language, target_lang: Language):
        try:
            prompt = f"""
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

                    Input word: {input}
                    Source language: {source_lang.name}
                    Target language: {target_lang.name}
                    """
            parsed_json = await self.fetch_ai_data(prompt, self.json_service.validate_dictionary_entry_json)
            return parsed_json
        except Exception as e:
            raise RuntimeError(f"Error fetching AI dictionary pos for '{input}'. {e}")

    async def fetch_ai_snippet_translation(self, snippet_text, translation_lang):
        try:
            prompt = f"""
                   Translate the input below to {translation_lang.name}.
                    Rules:
                    1. Respond ONLY with valid JSON. Do NOT include explanations, comments, or extra text.
                    2. Capitalize the first word only if required by grammar.
                    3. Break down input into individual words or tokens, including:
                       - "word": original word
                       - "part_of_speech": only include the **main POS label** (e.g., "verb"), not long explanations.
                       - "romanized": Latin script romanization
                       - "translations": at least three translation candidates if possible.
                    4. "romanized" must never contain non-Latin characters.
                    5. Use properly formatted JSON, double quotes, no trailing commas.

                    Output JSON format:

                    {{
                      "snippet_text": "<original input text>",
                      "translation": "<full translated sentence here>",
                      "word_parts": [
                        {{
                          "word": "<original word>",
                          "part_of_speech": "<part of speech>",
                          "romanized": "<romanized form in Latin>",
                          "translations": "<a list of at least three translation candidates if possible>"
                        }}
                      ]
                    }}

                    Input:
                    {snippet_text}
                    """
            parsed_json = await self.fetch_ai_data(prompt, self.json_service.validate_translation_json)
            return parsed_json
        except Exception as e:
            raise RuntimeError(f"Error fetching AI snippet translation for '{snippet_text}'. {e}")
