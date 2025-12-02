from app.stores import LanguageStore, TranslationStore, DictionaryStore, WordStore, SnippetStore
from models import Language, DictionaryPOS, Word
from .ai_service import AIService
from app.utils.helpers import is_single_word
from typing import List

class DictionaryService:
    def __init__(self, db):
        self.db = db
        self.translation_store = TranslationStore(db)
        self.language_store = LanguageStore(db)
        self.dictionary_store = DictionaryStore(db)
        self.word_store = WordStore(db)
        self.snippet_store = SnippetStore(db)
        self.ai_service = AIService()

    async def get_dictionary_entry(self, text: str, source_lang: Language, target_lang: Language):
        try:
            is_word = is_single_word(text)

            response = {
                "is_interpretable": False,
                "is_word": is_word,
                "data": None
            }

            if is_word:
                word = await self.word_store.get_word_by_text_and_lang(text, source_lang.id)
                if word:
                    response["is_interpretable"] = True
                    response["data"] = await self.get_word_dictionary(
                        word.text,
                        source_lang,
                        target_lang
                    )
                    return response
                
                interpretation = await self.ai_service.fetch_ai_text_interpretation(text)
                if not interpretation["is_interpretable"]:
                    return response
                
                source_lang = self.language_store.get_lang_by_code(interpretation["language_code"])
                response["is_interpretable"] = True
                response["data"] = await self.get_word_dictionary(
                    interpretation["normalized_text"],
                    source_lang,
                    target_lang
                )
                return response
            
            snippet = await self.snippet_store.get_snippet(text, source_lang)
            if snippet:
                response["is_interpretable"] = True
                response["data"] = await self.get_snippet_dictionary(
                    snippet.text,
                    source_lang,
                    target_lang
                )
            
            interpretation = await self.ai_service.fetch_ai_text_interpretation(text)
            if not interpretation["is_interpretable"]:
                return response
            
            source_lang = await self.language_store.get_lang_by_code(interpretation["language_code"])
            response["is_interpretable"] = True
            response["data"] = await self.get_snippet_dictionary(
                interpretation["normalized_text"],
                source_lang,
                target_lang
            )

            return response
        except Exception as e:
            raise RuntimeError(f"Error getting dictionary entry for '{text}'. {e}")

    async def get_normalized_word_dictionary_entry(self, word: Word, dictionary_pos_list: List[DictionaryPOS], target_lang: Language):
        try:
            word_translations = await self.translation_store.get_word_translations_by_lang(word.id, target_lang.id)
            snippet_translation_list = [
                await self.translation_store.get_snippet_translation_by_lang(pos.snippet_id, target_lang.id)
                for pos in dictionary_pos_list
            ]
            word_ids = {sw.word_id for pos in dictionary_pos_list for sw in pos.snippet.snippet_words}
            snippet_word_translations_map = {
                wid: await self.translation_store.get_word_translations_by_lang(wid, target_lang.id)
                for wid in word_ids
            }

            return {
                "word": word.text,
                "word_id": word.id,
                "romanized": word.romanized,
                "phonetic_spelling": word.phonetic_spelling,
                "source_lang_code": word.language.code,
                "target_lang_code": target_lang.code,
                "translations": [t.text for t in word_translations],
                "parts_of_speech": [{
                    "name": pos.name,
                    "definition": pos.description,
                    "example_words": [{
                        "text": w.text,
                        "part_of_speech": w.part_of_speech_tag,
                        "romanized": w.word.romanized,
                        "translations": [{"text": t.text} for t in snippet_word_translations_map[w.word_id]],
                        "order_index": w.order_index
                    } for w in pos.snippet.snippet_words],
                    "example_translation": snippet_translation_list[i].text
                } for i, pos in enumerate(dictionary_pos_list)]
            }

        except Exception as e:
            raise RuntimeError(f"Error getting normalized dictionary entry for word ID '{word.id}'. {e}")

    async def get_word_dictionary(self, text: str, source_lang: Language, target_lang: Language):
        try:
            word = await self.word_store.get_word_by_text_and_lang(text, source_lang.id)

            if word:
                # check if POS exists for this word in target language
                dictionary_pos_list = await self.dictionary_store.get_word_dictionary_pos_list_by_lang(word.id, target_lang.id)
                if dictionary_pos_list:
                    return await self.get_normalized_word_dictionary_entry(word, dictionary_pos_list, target_lang)
                else:
                    # fetch POS from AI and save
                    dictionary_pos_data = await self.ai_service.fetch_ai_dictionary_pos(
                        text,
                        source_lang,
                        target_lang
                    )
                    await self.dictionary_store.save_word_pos_list(
                        word.id,
                        dictionary_pos_data,
                        source_lang,
                        target_lang
                    )
                    dictionary_pos_list = await self.dictionary_store.get_word_dictionary_pos_list_by_lang(word.id, target_lang.id)
                    return await self.get_normalized_word_dictionary_entry(word, dictionary_pos_list, target_lang)
            
            dictionary_entry = await self.ai_service.fetch_ai_dictionary_entry(
                text,
                source_lang,
                target_lang
            )
            word_id = await self.dictionary_store.save_word_dictionary_entry(
                dictionary_entry,
                source_lang,
                target_lang
            )
            word = await self.word_store.get_word_by_id(word_id)
            dictionary_pos_list = await self.dictionary_store.get_word_dictionary_pos_list_by_lang(word.id, target_lang.id)

            return await self.get_normalized_word_dictionary_entry(word, dictionary_pos_list, target_lang)
        except Exception as e:
            raise RuntimeError(f"Error getting word dictionary for '{text}'. {e}")

    async def get_snippet_dictionary(self, text: str, source_lang: Language, target_lang: Language):
        try:
            snippet_id = await self.snippet_store.save_snippet(text, source_lang)
    
            snippet_translation = await self.translation_store.get_snippet_translation_by_lang(snippet_id, target_lang.id)
            if snippet_translation is None:
                ai_data = await self.ai_service.fetch_ai_snippet_translation(text, target_lang)
                snippet_translation_id = await self.translation_store.save_ai_snippet_translation(snippet_id, source_lang, target_lang, ai_data)
                snippet_translation = await self.translation_store.get_snippet_translation_by_id(snippet_translation_id)

            snippet = await self.snippet_store.get_snippet_by_id(snippet_id)

            word_ids = {sw.word_id for sw in snippet.snippet_words}
            snippet_word_translations_map = {
                wid: await self.translation_store.get_word_translations_by_lang(wid, target_lang.id)
                for wid in word_ids
            }

            return {
                "text": snippet.text,
                "translation": snippet_translation.text,
                "source_lang_code": source_lang.code,
                "target_lang_code": target_lang.code,
                "snippet_words": [{
                    "text": w.text,
                    "part_of_speech": w.part_of_speech_tag,
                    "romanized": w.word.romanized,
                    "translations": [{"text": t.text} for t in snippet_word_translations_map[w.word_id]],
                    "order_index": w.order_index
                } for w in snippet.snippet_words]
            }

        except Exception as e:
            raise RuntimeError(f"Error getting phrase dictionary for '{text}'. {e}")