import aiosqlite
import asyncio
import os

from database import DATABASE_PATH


async def create_database():
    # Создаём директорию если нет
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Таблица для изображений (BLOB) и контекста
        await db.execute('''
            CREATE TABLE IF NOT EXISTS images (
                user_id INTEGER PRIMARY KEY,
                photo BLOB,
                context TEXT,
                latitude REAL,
                longitude REAL,
                full_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')

        # Таблица для ответов LLM
        await db.execute('''
            CREATE TABLE IF NOT EXISTS LLM_replies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                context TEXT,
                photo BLOB,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # WAL mode для лучшей concurrency в async
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        await db.execute("PRAGMA cache_size=10000")

        await db.commit()
        print(f"✅ База данных создана/обновлена: {DATABASE_PATH}")


if __name__ == "__main__":
    asyncio.run(create_database())
