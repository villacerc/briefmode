
from .json_validators import validate_interpretation_json, validate_dictionary_entry_json
from .helpers import fetch_ai_data
from app.stores import LanguageStore, TranslationStore, DictionaryStore, WordStore
from models import Language, DictionaryPOS, Word

class DictionaryService:
    def __init__(self, db):
        self.db = db
        self.translation_store = TranslationStore(db)
        self.language_store = LanguageStore(db)
        self.dictionary_store = DictionaryStore(db)
        self.word_store = WordStore(db)

    async def get_dictionary_entry(self, text: str, target_lang: Language):
        try:
            interpretation = await self.fetch_ai_text_interpretation(text)

            if interpretation["is_interpretable"]:
                # TODO: check if text exists in DB
                source_lang = self.language_store.get_by_code(interpretation["language_code"])

                word = self.word_store.get_word_by_lang(interpretation["normalized_text"], source_lang.id)
                if word is not None:
                    # check if POS exists for this word in target language
                    dictionary_pos_list = self.dictionary_store.get_word_dictionary_pos_by_lang(word.id, target_lang.id)
                    if len(dictionary_pos_list) > 0:
                        data = self.get_normalized_dictionary_entry(word, target_lang)
                        return {
                            "is_interpretable": True,
                            "is_word": interpretation["is_word"],
                            "data": data
                        }

                # TEMPORARY: assumes text is a word, not a phrase
                source_lang = self.language_store.get_by_code(interpretation["language_code"])
    
                dictionary_entry = await self.fetch_ai_dictionary_entry(
                    interpretation["normalized_text"],
                    source_lang,
                    target_lang
                )

                word = await self.dictionary_store.save_word_dictionary_entry(
                    dictionary_entry,
                    source_lang,
                    target_lang
                )

                data = self.get_normalized_dictionary_entry(word, target_lang)
                return {
                    "is_interpretable": True,
                    "is_word": interpretation["is_word"],
                    "data": data
                }
            else:
                return {
                    "is_interpretable": False,
                    "data": None
                }

        except Exception as e:
            raise RuntimeError(f"Error getting dictionary entry for '{text}'. {e}")

    def get_normalized_dictionary_entry(self, word: Word, target_lang: Language):
        try:
            translations = self.translation_store.get_word_translations_by_lang(word.id, target_lang.id)
            dictionary_pos = self.dictionary_store.get_word_dictionary_pos_by_lang(word.id, target_lang.id)

            return {
                "word": word.text,
                "romanized": word.romanized,
                "translations": [t.text for t in translations],
                "parts_of_speech": [{
                    "name": pos.name,
                    "definition": pos.description,
                    "example": pos.example,
                    "example_translation": pos.normalized_example.translations[0].text
                } for pos in dictionary_pos]
            }
        except Exception as e:
            raise RuntimeError(f"Error getting normalized dictionary entry for word ID '{word.id}'. {e}")

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
            parsed_json = await fetch_ai_data(prompt, validate_interpretation_json)
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
            parsed_json = await fetch_ai_data(prompt, validate_dictionary_entry_json)
            return parsed_json
        except Exception as e:
            raise RuntimeError(f"Error fetching AI dictionary entry for '{input}'. {e}")
