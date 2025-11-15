from models import Language
from database import get_db, create_tables, drop_tables
import requests
from sqlalchemy.exc import SQLAlchemyError
import json
from pathlib import Path

def seed():
    drop_tables()
    create_tables()

    seed_languages()

def seed_languages():
    db = next(get_db())
    try:
        # Get path of the JSON file relative to this script
        file_path = Path(__file__).parent / "lang_map.json"
        
        with open(file_path, "r", encoding="utf-8") as f:
            lang_map = json.load(f)

        for iso_code, data in lang_map.items():
            language = Language(code=iso_code, name=data["name"], bcp47_code=data["bcp47"].lower())
            db.add(language)

        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to seed languages: {e}")
    finally:
        db.close()

if __name__ == '__main__':
    seed()