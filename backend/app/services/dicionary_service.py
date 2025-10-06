from app.stores import LanguageStore, TranslationStore, DictionaryStore, WordStore
from models import Language, DictionaryPOS, Word
from .ai_service import AIService

class DictionaryService:
    def __init__(self, db):
        self.db = db
        self.translation_store = TranslationStore(db)
        self.language_store = LanguageStore(db)
        self.dictionary_store = DictionaryStore(db)
        self.word_store = WordStore(db)
        self.ai_service = AIService()

    async def get_dictionary_entry(self, text: str, target_lang: Language):
        try:
            interpretation = await self.ai_service.fetch_ai_text_interpretation(text)

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
                    else:
                        # fetch POS from AI and save
                        dictionary_pos = await self.ai_service.fetch_ai_dictionary_pos(
                            interpretation["normalized_text"],
                            source_lang,
                            target_lang
                        )
                        word = await self.dictionary_store.save_word_pos_entry(
                            word,
                            dictionary_pos,
                            source_lang,
                            target_lang
                        )
                        data = self.get_normalized_dictionary_entry(word, target_lang)
                        return {
                            "is_interpretable": True,
                            "is_word": interpretation["is_word"],
                            "data": data
                        }

                # TEMPORARY: assumes text is a word, not a phrase
                source_lang = self.language_store.get_by_code(interpretation["language_code"])

                dictionary_entry = await self.ai_service.fetch_ai_dictionary_entry(
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

    
