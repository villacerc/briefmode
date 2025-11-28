from models import Language
from database import AsyncSessionLocal, get_db, create_tables, drop_tables
import requests
from sqlalchemy.exc import SQLAlchemyError
import json
from pathlib import Path
import asyncio

async def seed():
    await drop_tables()
    await create_tables()

    await seed_languages()

async def seed_languages():
    file_path = Path(__file__).parent / "lang_map.json"

    async with AsyncSessionLocal() as db:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lang_map = json.load(f)

            for iso_code, data in lang_map.items():
                language = Language(
                    code=iso_code,
                    name=data["name"],
                    bcp47_code=data["bcp47"].lower()
                )
                db.add(language)

            await db.commit()
            print("Seed successful.")
        except Exception as e:
            await db.rollback()
            print(f"Failed to seed: {e}")

if __name__ == '__main__':
    asyncio.run(seed())