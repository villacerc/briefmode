from app.stores import LanguageStore, TranslationStore, DictionaryStore, WordStore, SnippetStore
from models import Language, DictionaryPOS, Word
from .ai_service import AIService

class DictionaryService:
    def __init__(self, db):
        self.db = db
        self.translation_store = TranslationStore(db)
        self.language_store = LanguageStore(db)
        self.dictionary_store = DictionaryStore(db)
        self.word_store = WordStore(db)
        self.snippet_store = SnippetStore(db)
        self.ai_service = AIService()

    async def get_dictionary_entry(self, text: str, target_lang: Language):
        try:
            interpretation = await self.ai_service.fetch_ai_text_interpretation(text)

            response = {
                "is_interpretable": interpretation["is_interpretable"],
                "is_word": interpretation["is_word"],
                "data": None
            }

            if not interpretation["is_interpretable"]:
                return response

            source_lang = self.language_store.get_by_code(interpretation["language_code"])

            if interpretation["is_word"]:
                response["data"] = await self.get_word_dictionary(
                    interpretation["normalized_text"],
                    source_lang,
                    target_lang
                )
            else:
                response["data"] = await self.get_snippet_dictionary(
                    interpretation["normalized_text"],
                    source_lang,
                    target_lang
                )

            return response
        except Exception as e:
            raise RuntimeError(f"Error getting dictionary entry for '{text}'. {e}")

    def get_normalized_word_dictionary_entry(self, word: Word, target_lang: Language):
        try:
            translations = self.translation_store.get_word_translations_by_lang(word.id, target_lang.id)
            dictionary_pos = self.dictionary_store.get_word_dictionary_pos_by_lang(word.id, target_lang.id)

            return {
                "word": word.text,
                "romanized": word.romanized,
                "phonetic_spelling": word.phonetic_spelling,
                "source_lang_code": word.language.code,
                "translations": [t.text for t in translations],
                "parts_of_speech": [{
                    "name": pos.name,
                    "definition": pos.description,
                    "example_words": [{
                        "text": w.text,
                        "part_of_speech": w.part_of_speech_tag,
                        "romanized": w.word.romanized,
                        "translations": [{"text": t.text} for t in w.word.translations],
                        "order_index": w.order_index
                    } for w in pos.normalized_example.snippet_words],
                    "example_translation": pos.normalized_example.translations[0].text
                } for pos in dictionary_pos]
            }

        except Exception as e:
            raise RuntimeError(f"Error getting normalized dictionary entry for word ID '{word.id}'. {e}")

    async def get_word_dictionary(self, text: str, source_lang: Language, target_lang: Language):
        try:
            word = self.word_store.get_word_by_lang(text, source_lang.id)

            if word is not None:
                # check if POS exists for this word in target language
                dictionary_pos_list = self.dictionary_store.get_word_dictionary_pos_by_lang(word.id, target_lang.id)
                if len(dictionary_pos_list) > 0:
                    return self.get_normalized_word_dictionary_entry(word, target_lang)
                else:
                    # fetch POS from AI and save
                    dictionary_pos = await self.ai_service.fetch_ai_dictionary_pos(
                        text,
                        source_lang,
                        target_lang
                    )
                    word = await self.dictionary_store.save_word_pos_entry(
                        word,
                        dictionary_pos,
                        source_lang,
                        target_lang
                    )
                    return self.get_normalized_word_dictionary_entry(word, target_lang)
            
            dictionary_entry = await self.ai_service.fetch_ai_dictionary_entry(
                text,
                source_lang,
                target_lang
            )

            word = await self.dictionary_store.save_word_dictionary_entry(
                dictionary_entry,
                source_lang,
                target_lang
            )

            return self.get_normalized_word_dictionary_entry(word, target_lang)
        except Exception as e:
            raise RuntimeError(f"Error getting word dictionary for '{text}'. {e}")

    async def get_snippet_dictionary(self, text: str, source_lang: Language, target_lang: Language):
        try:
            snippet = self.snippet_store.save_snippet(text, source_lang.id)

            snippet_translation = self.translation_store.get_snippet_translation_by_lang(snippet.id, target_lang.id)

            if snippet_translation is None:
                ai_data = await self.ai_service.fetch_ai_snippet_translation(snippet.text, target_lang)
                snippet_translation = self.translation_store.save_ai_snippet_translation(snippet, target_lang, ai_data)

            snippet_words = snippet.snippet_words

            return {
                "text": snippet.text,
                "translation": snippet_translation.text,
                "source_lang_code": source_lang.code,
                "target_lang_code": target_lang.code,
                "snippet_words": [{
                    "text": w.text,
                    "part_of_speech": w.part_of_speech_tag,
                    "romanized": w.word.romanized,
                    "translations": [{"text": t.text} for t in w.word.translations],
                    "order_index": w.order_index
                } for w in snippet_words]
            }

        except Exception as e:
            raise RuntimeError(f"Error getting phrase dictionary for '{text}'. {e}")