from app.stores import LanguageStore, WordPOSSnippetStore, WordStore, SnippetStore, WordTranslationStore, SnippetTranslationStore
from models import Language, Snippet, Word, AIPromptType, SnippetTranslation
from .ai_service import AIService
from .translation_service import TranslationService
from app.utils.helpers import sanitize_snippet_text, sanitize_word
from collections import defaultdict

class DictionaryService:
    def __init__(self, db):
        self.db = db
        self.word_translation_store = WordTranslationStore(db)
        self.snippet_translation_store = SnippetTranslationStore(db)
        self.language_store = LanguageStore(db)
        self.word_pos_snippet_store = WordPOSSnippetStore(db)
        self.word_store = WordStore(db)
        self.snippet_store = SnippetStore(db)
        self.ai_service = AIService()
        self.translation_service = TranslationService(db)

    async def get_dictionary_entry(self, text: str, source_lang: Language, target_lang: Language):
        try:
            word = await self.word_store.get_word_by_text_and_lang(text, source_lang.id)
            if word:
                await self.generate_dictionary_for_existing_word(word, word.language, target_lang)
                await self.db.commit()
                data = await self.get_normalized_word_dictionary_entry(word, target_lang)
                return {
                    "is_interpretable": True,
                    "is_word": True,
                    "data": data
                }

            # check if text is a phrase that exists in DB
            snippet = await self.snippet_store.get_snippet_by_text(sanitize_snippet_text(text), True)
            if snippet:
                snippet_translations = await self.snippet_translation_store.get_snippet_translations_by_lang([snippet.id], target_lang.id)
                if not snippet_translations:
                    await self.generate_dictionary_for_existing_snippet(snippet, snippet.language, target_lang)
                    await self.db.commit()
                    snippet_translations = await self.snippet_translation_store.get_snippet_translations_by_lang([snippet.id], target_lang.id)
                data = await self.get_normalized_snippet_dictionary_entry(snippet, snippet_translations[0], target_lang)
                return {
                    "is_interpretable": True,
                    "is_word": False,
                    "data": data
                }
            
            interpretation = await self.ai_service.fetch_ai_data(AIPromptType.TEXT_INTERPRETATION, {}, {"text": text})
            if not interpretation["is_interpretable"]:
                return {
                    "is_interpretable": False,
                    "is_word": False,
                    "data": None
                }
            
            source_lang = await self.language_store.get_lang_by_code(interpretation["language_code"])

            if interpretation["is_word"]:
                text = interpretation["normalized_text"]
                await self.generate_dictionary_for_new_word(text, source_lang, target_lang)
                await self.db.commit()
                word = await self.word_store.get_word_by_text_and_lang(text, source_lang.id)
                data = await self.get_normalized_word_dictionary_entry(word, target_lang)
                return {
                    "is_interpretable": True,
                    "is_word": True,
                    "data": data
                }

            await self.generate_dictionary_for_new_snippet(text, source_lang, target_lang)
            await self.db.commit()
            snippet = await self.snippet_store.get_snippet_by_text(sanitize_snippet_text(text), True)
            snippet_translations = await self.snippet_translation_store.get_snippet_translations_by_lang([snippet.id], target_lang.id)
            data = await self.get_normalized_snippet_dictionary_entry(snippet, snippet_translations[0], target_lang)
            return {
                "is_interpretable": True,
                "is_word": False,
                "data": data
            }

        except Exception as e:
            raise RuntimeError(f"Error getting dictionary entry for '{text}'. {e}")

    async def generate_dictionary_for_existing_word(self, word: Word, source_lang: Language, target_lang: Language):
        try:
            # check if POS exists for this word
            word_pos_snippets = await self.word_pos_snippet_store.get_word_pos_snippets(word.id, eager_load=True)
            if word_pos_snippets:
                pos_snippet_translations = await self.snippet_translation_store.get_snippet_translations_by_lang([pos_snippet.snippet.id for pos_snippet in word_pos_snippets], target_lang.id)
                if not pos_snippet_translations:
                    await self.translation_service.generate_snippet_translations_and_word_translations_for_existing_snippet_words([pos_snippet.snippet for pos_snippet in word_pos_snippets], target_lang)
            else:
                # fetch POS from AI and save
                ai_word_dictionary_data = await self.ai_service.fetch_ai_data(AIPromptType.WORD_POS, {"source_lang_name": source_lang.name, "target_lang_name": target_lang.name}, {"text": word.text})
                new_pos_snippets = [pos["example"] for pos in ai_word_dictionary_data["parts_of_speech"]]
                if new_pos_snippets:
                    added_pos_snippets = await self.snippet_store.add_snippets(new_pos_snippets, source_lang.id)
                    await self.translation_service.generate_snippet_translations_and_word_translations(added_pos_snippets, source_lang, target_lang)
                    await self.word_pos_snippet_store.add_word_pos_snippets_batch(word.id, added_pos_snippets, ai_word_dictionary_data["parts_of_speech"])
        except Exception as e:
            raise RuntimeError(f"Error getting dictionary for existing word: id '{word.id}'. {e}")

    async def generate_dictionary_for_new_word(self, text: str, source_lang: Language, target_lang: Language):
        try:
            ai_word_dictionary_data = await self.ai_service.fetch_ai_data(AIPromptType.WORD_DICTIONARY, {"source_lang_name": source_lang.name, "target_lang_name": target_lang.name}, {"text": text})
            word_map = await self.word_store.save_ai_words_batch([ai_word_dictionary_data], source_lang.id)
            word_id = word_map[(sanitize_word(ai_word_dictionary_data["word"]), source_lang.id)]
            new_pos_snippets = [pos["example"] for pos in ai_word_dictionary_data["parts_of_speech"]]
            added_pos_snippets = await self.snippet_store.add_snippets(new_pos_snippets, source_lang.id)
            await self.translation_service.generate_snippet_translations_and_word_translations(added_pos_snippets, source_lang, target_lang)
            await self.word_pos_snippet_store.add_word_pos_snippets_batch(word_id, added_pos_snippets, ai_word_dictionary_data["parts_of_speech"])
        except Exception as e:
            raise RuntimeError(f"Error getting word dictionary for new word '{text}'. {e}")

    async def get_normalized_word_dictionary_entry(self, word: Word, target_lang: Language):
        try:
            word_pos_snippets = await self.word_pos_snippet_store.get_word_pos_snippets(word.id, eager_load=True)
            word_translations = await self.word_translation_store.get_word_translations_batch_by_lang([word.id], target_lang.id)
            snippet_ids = [p.snippet_id for p in word_pos_snippets]
            snippet_translation_list = await self.snippet_translation_store.get_snippet_translations_by_lang(snippet_ids, target_lang.id, eager_load=True)
            word_ids = {sw.word_id for pos in word_pos_snippets for sw in pos.snippet.snippet_words}
            snippet_word_translations = await self.word_translation_store.get_word_translations_batch_by_lang(word_ids, target_lang.id)
            snippet_word_translations_map = defaultdict(list)
            for t in snippet_word_translations:
                snippet_word_translations_map[t.word_id].append(t)

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
                } for i, pos in enumerate(word_pos_snippets)]
            }

        except Exception as e:
            raise RuntimeError(f"Error getting normalized dictionary entry for word ID '{word.id}'. {e}")

    async def generate_dictionary_for_existing_snippet(self, snippet: Snippet, source_lang: Language, target_lang: Language):
        try:
            if snippet.snippet_words:
                await self.translation_service.generate_snippet_translations_and_word_translations_for_existing_snippet_words([snippet], target_lang)
            else:
                await self.translation_service.generate_snippet_translations_and_word_translations([snippet], source_lang, target_lang)
        except Exception as e:
            raise RuntimeError(f"Error getting dictionary for existing snippet with id '{snippet.id}'. {e}")

    async def generate_dictionary_for_new_snippet(self, text: str, source_lang: Language, target_lang: Language):
        try:
            added_snippets = await self.snippet_store.add_snippets([sanitize_snippet_text(text)], source_lang.id)
            await self.translation_service.generate_snippet_translations_and_word_translations(added_snippets, source_lang, target_lang)
        except Exception as e:
            raise RuntimeError(f"Error getting dictionary for new snippet '{text}'. {e}")
        
    async def get_normalized_snippet_dictionary_entry(self, snippet: Snippet, snippet_translation: SnippetTranslation, target_lang: Language):
        try:  
            word_ids = [sw.word_id for sw in snippet.snippet_words]
            word_translations = await self.word_translation_store.get_word_translations_batch_by_lang(word_ids, target_lang.id)
            word_translations_map = defaultdict(list)
            for t in word_translations:
                word_translations_map[t.word_id].append(t)

            return {
                "text": snippet.text,
                "translation": snippet_translation.text,
                "source_lang_code": snippet.language.code,
                "target_lang_code": target_lang.code,
                "snippet_words": [{
                    "text": w.text,
                    "part_of_speech": w.part_of_speech_tag,
                    "romanized": w.word.romanized,
                    "translations": [{"text": t.text} for t in word_translations_map[w.word_id]],
                    "order_index": w.order_index
                } for w in snippet.snippet_words]
            }

        except Exception as e:
            raise RuntimeError(f"Error getting normalized snippet dictionary for snippet id '{snippet.id}'. {e}")