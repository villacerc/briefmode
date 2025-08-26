from models import Language
from database import get_db, create_tables, drop_tables
import requests
from sqlalchemy.exc import SQLAlchemyError

def seed():
    drop_tables()
    create_tables()

    seed_languages()

def seed_languages():
    db = next(get_db())
    try:
        url = "https://gist.githubusercontent.com/josantonius/b455e315bc7f790d14b136d61d9ae469/raw/416def353b8849c427e9062a9db6445c62e77f75/language-codes.json"
        response = requests.get(url)
        languages_data = response.json()

        for code, name in languages_data.items():
            language = Language(code=code, name=name)
            db.add(language)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to seed languages: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    seed()