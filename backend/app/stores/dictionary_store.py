from models import DictionaryPOS, Snippet, Word, SnippetTranslation, Language
from sqlalchemy.orm import Session
from .translation_store import TranslationStore
from .word_store import WordStore
from app.utils.helpers import sanitize_phrase
from app.services.ai_service import AIService
from typing import List

class DictionaryStore:
    def __init__(self, db: Session):
        self.db = db
        self.word_store = WordStore(db)
        self.translation_store = TranslationStore(db)
        self.ai_service = AIService()

    def get_word_dictionary_pos_by_lang(self, word_id: int, target_lang_id: int) -> List[DictionaryPOS]:
        return self.db.query(DictionaryPOS).join(Snippet).join(Snippet.translations).filter(
            DictionaryPOS.word_id == word_id,
            SnippetTranslation.language_id == target_lang_id
        ).all()

    async def save_word_dictionary_entry(self, data: dict, source_lang: Language, target_lang: Language) -> Word:
        word = self.word_store.save_word(
            word_text=data["word"],
            romanized=data["romanized"],
            translations=data["translations"],
            source_lang_id=source_lang.id,
            target_lang_id=target_lang.id,
        )

        await self.save_word_pos_entry(word, data, source_lang, target_lang)

        return word
    
    async def save_word_pos_entry(self, word: Word, data: dict, source_lang: Language, target_lang: Language) -> Word:
        pos_data = data["parts_of_speech"]

        for pos in pos_data:
            snippet = Snippet(
                text=sanitize_phrase(pos["example"]),
                language_id=source_lang.id,
            )
            self.db.add(snippet)
            self.db.flush()
            part_of_speech = DictionaryPOS(
                snippet_id=snippet.id,
                word_id=word.id,
                name=pos["part_of_speech"],
                description=pos["definition"],
                example=pos["example"],
            )
            self.db.add(part_of_speech)

            # Fetch and save example translation
            translation_json = await self.ai_service.fetch_ai_snippet_translation(pos["example"], target_lang)
            self.translation_store.save_snippet_translation(snippet, target_lang, translation_json)

        self.db.commit()

        return word