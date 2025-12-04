from models import DictionaryPOS, Snippet, Word, SnippetTranslation, Language, SnippetWord
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from .translation_store import TranslationStore
from .word_store import WordStore
from .snippet_store import SnippetStore
from app.services.ai_service import AIService
from typing import List

DICTIONARY_POS_QUERY_OPTIONS = (
    selectinload(DictionaryPOS.snippet)
        .selectinload(Snippet.snippet_words)
        .selectinload(SnippetWord.word),
    selectinload(DictionaryPOS.word)
        .selectinload(Word.language),
    selectinload(DictionaryPOS.language)
)

class DictionaryStore:
    def __init__(self, db: Session):
        self.db = db
        self.word_store = WordStore(db)
        self.translation_store = TranslationStore(db)
        self.snippet_store = SnippetStore(db)
        self.ai_service = AIService()

    async def get_dictionary_pos_by_id(self, pos_id: int, eager_load: bool = False) -> List[DictionaryPOS]:
        query = select(DictionaryPOS).where(DictionaryPOS.id == pos_id)
        if eager_load:
            query = query.options(*DICTIONARY_POS_QUERY_OPTIONS)

        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_word_dictionary_pos_list_by_lang(self, word_id: int, target_lang_id: int, eager_load: bool = False) -> List[DictionaryPOS]:
        query = select(DictionaryPOS).where(
            DictionaryPOS.word_id == word_id,
            DictionaryPOS.language_id == target_lang_id
        )
        if eager_load:
            query = query.options(*DICTIONARY_POS_QUERY_OPTIONS)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def save_word_dictionary_entry(self, data: dict, source_lang: Language, target_lang: Language) -> int:
        word_id = await self.word_store.save_word(
            data=data,
            source_lang_id=source_lang.id
        )

        await self.save_word_pos_list(word_id, data, source_lang, target_lang)
    
        return word_id
    
    async def save_dictionary_pos(self, word_id: int, data: dict, source_lang: Language, target_lang: Language) -> int:
        existing_pos_result = await self.db.execute(
            select(DictionaryPOS).where(
                DictionaryPOS.word_id == word_id,
                DictionaryPOS.language_id == target_lang.id,
                DictionaryPOS.name == data["part_of_speech"],
            )
        )
        existing_pos = existing_pos_result.scalars().first()

        if existing_pos:
            return existing_pos.id

        snippet_id = await self.snippet_store.save_snippet(data["example"], source_lang)

        part_of_speech = DictionaryPOS(
            word_id=word_id,
            language_id=target_lang.id,
            snippet_id=snippet_id,
            name=data["part_of_speech"],
            description=data["definition"],
        )
        self.db.add(part_of_speech)
        await self.db.commit()

        return part_of_speech.id
    
    async def save_word_pos_list(self, word_id: int, data: dict, source_lang: Language, target_lang: Language):
        pos_data = data["parts_of_speech"]

        # TODO: Run in parallel
        for pos in pos_data:
            dictionary_pos_id = await self.save_dictionary_pos(word_id, pos, source_lang, target_lang)
            dictionary_pos = await self.get_dictionary_pos_by_id(dictionary_pos_id)
            
            # Fetch and save example translation
            translation_json = await self.ai_service.fetch_ai_snippet_translation(pos["example"], target_lang)
            await self.translation_store.save_ai_snippet_translation(dictionary_pos.snippet_id, source_lang, target_lang, translation_json)

        await self.db.commit()