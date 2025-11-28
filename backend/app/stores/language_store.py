from models import Language
from sqlalchemy import select

class LanguageStore:
    def __init__(self, db):
        self.db = db

    def language_exists(self, code: str) -> bool:
        return self.db.query(Language).filter(Language.code == code).first() is not None

    async def get_by_code(self, code: str):
        try:
            result = await self.db.execute(select(Language).where(Language.code == code))
            language = result.scalars().first()
            if not language:
                raise ValueError(f"Language with code '{code}' not found.")
            return language
        except Exception as e:
            raise RuntimeError(f"Error fetching language with code '{code}'. {e}")

    def create(self, code: str, name: str):
        language = Language(code=code, name=name)
        self.db.add(language)
        self.db.commit()
        self.db.refresh(language)
        return language
    