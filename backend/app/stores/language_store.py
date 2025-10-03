from models import Language

class LanguageStore:
    def __init__(self, db):
        self.db = db

    def language_exists(self, code: str) -> bool:
        return self.db.query(Language).filter(Language.code == code).first() is not None

    def get_by_code(self, code: str):
        try:
            language = self.db.query(Language).filter(Language.code == code).first()
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
    