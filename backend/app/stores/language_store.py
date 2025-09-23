from models import Language

class LanguageStore:
    def __init__(self, db):
        self.db = db

    def get_by_code(self, code: str):
        return self.db.query(Language).filter(Language.code == code).first()

    def create(self, code: str, name: str):
        language = Language(code=code, name=name)
        self.db.add(language)
        self.db.commit()
        self.db.refresh(language)
        return language
    