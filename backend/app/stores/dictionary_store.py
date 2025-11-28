from models import DictionaryPOS, Snippet, Word, SnippetTranslation, Language, SnippetWord
from sqlalchemy.orm import Session, selectinload
from .translation_store import TranslationStore
from .word_store import WordStore
from .snippet_store import SnippetStore
from app.services.ai_service import AIService
from typing import List

class DictionaryStore:
    def __init__(self, db: Session):
        self.db = db
        self.word_store = WordStore(db)
        self.translation_store = TranslationStore(db)
        self.snippet_store = SnippetStore(db)
        self.ai_service = AIService()

    def get_word_dictionary_pos_by_lang(self, word_id: int, target_lang_id: int) -> List[DictionaryPOS]:
        return (
            self.db.query(DictionaryPOS)
            .options(
                selectinload(DictionaryPOS.snippet)
                    .selectinload(Snippet.snippet_words)
                    .selectinload(SnippetWord.word)
                    .selectinload(Word.translations),
                selectinload(DictionaryPOS.word),
            )
            .filter(
                DictionaryPOS.word_id == word_id,
                DictionaryPOS.language_id == target_lang_id
            )
            .all()
        )

    async def save_word_dictionary_entry(self, data: dict, source_lang: Language, target_lang: Language) -> Word:
        word = self.word_store.save_word(
            data=data,
            source_lang_id=source_lang.id,
            target_lang_id=target_lang.id,
        )

        await self.save_word_pos_entry(word, data, source_lang, target_lang)

        return word
    
    def save_dictionary_pos(self, word: Word, data: dict, source_lang: Language, target_lang: Language) -> DictionaryPOS:
        existing_pos = self.db.query(DictionaryPOS).filter(
            DictionaryPOS.word_id == word.id,
            DictionaryPOS.name == data["part_of_speech"]
        ).first()

        if existing_pos:
            return existing_pos

        snippet = self.snippet_store.save_snippet(data["example"], source_lang)

        part_of_speech = DictionaryPOS(
            word_id=word.id,
            language_id=target_lang.id,
            snippet_id=snippet.id,
            name=data["part_of_speech"],
            description=data["definition"],
        )
        self.db.add(part_of_speech)
        self.db.flush()

        return part_of_speech
    
    async def save_word_pos_entry(self, word: Word, data: dict, source_lang: Language, target_lang: Language) -> Word:
        pos_data = data["parts_of_speech"]

        # TODO: Run in parallel
        for pos in pos_data:
            dictionary_pos = self.save_dictionary_pos(word, pos, source_lang, target_lang)
            
            # Fetch and save example translation
            translation_json = await self.ai_service.fetch_ai_snippet_translation(pos["example"], target_lang)
            self.translation_store.save_ai_snippet_translation(dictionary_pos.snippet, target_lang, translation_json)

        self.db.commit()

        return word