from models import Language
from sqlalchemy import select

class LanguageStore:
    def __init__(self, db):
        self.db = db

    async def get_lang_by_id(self, language_id: int):
        result = await self.db.execute(select(Language).where(Language.id == language_id))
        return result.scalars().first()

    async def get_lang_by_code(self, code: str):
        try:
            result = await self.db.execute(select(Language).where(Language.code == code))
            language = result.scalars().first()
            if not language:
                raise ValueError(f"Language with code '{code}' not found.")
            return language
        except Exception as e:
            raise RuntimeError(f"Error fetching language with code '{code}'. {e}")

    async def save_language(self, data: dict):
        existing_language = await self.get_lang_by_code(data["code"])
        if existing_language:
            return existing_language.id

        language = Language(code=data["code"], name=data["name"])
        self.db.add(language)
        self.db.commit()

        return language.id
    