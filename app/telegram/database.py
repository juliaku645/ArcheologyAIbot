import aiosqlite
import asyncio
import os
from dotenv import load_dotenv
# DATABASE_PATH = r"C:\projects\ArcheologyAIbot\app\telegram\images_blob.db"
load_dotenv()

DATABASE_PATH = os.getenv("DB_PATH")
class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.db = None
        self.db_lock = asyncio.Lock()

    async def connect(self):
        self.db = await aiosqlite.connect(self.db_path, timeout=30)
        await self.db.execute("PRAGMA journal_mode=WAL")
        await self.db.commit()

    async def close(self):
        await self.db.close()

    async def save_or_update_image(self, user_id: int, image_bytes: bytes,context_text: str=None):
        async with self.db_lock:
            async with self.db.execute("SELECT 1 FROM images WHERE user_id=?", (user_id,)) as cursor:
                exists = await cursor.fetchone()
            if exists:
                await self.db.execute("UPDATE images SET photo=?, context=? WHERE user_id=?", (image_bytes, context_text, user_id))
            else:
                await self.db.execute("INSERT INTO images (user_id,  photo, context) VALUES (?, ?, ?)", (user_id, image_bytes, context_text))
            await self.db.commit()
    async def update_text(self, user_id: int, context_text: str):
        async with self.db_lock:
            async with self.db.execute("SELECT 1 FROM images WHERE user_id=?", (user_id,)) as cursor:
                exists = await cursor.fetchone()
            if exists:
                await self.db.execute("UPDATE images SET context=? WHERE user_id=?",(context_text,user_id))
            else:
                await self.db.execute("INSERT INTO images (user_id, context) VALUES (?, ?)",
                                      (user_id, context_text))
            await self.db.commit()
            print("Текст сохранен в БД")

    async def get_image_blob(self, user_id: int):
        async with self.db_lock:
            async with self.db.execute("SELECT photo FROM images WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
                return None

    async def get_context(self, user_id: int):
        async with self.db_lock:
            async with self.db.execute("SELECT context FROM images WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] or "" if row else ""

    async def save_description(self, user_id: int, context_text: str, image_bytes: bytes,description: str):
        async with self.db_lock:
            async with self.db.execute("INSERT INTO LLM_replies (user_id, context, photo,description) VALUES (?, ?, ?, ?)", (user_id, context_text,image_bytes, description)):
                await self.db.commit()

    async def save_geo_with_address(self, user_id: int, latitude: float, longitude: float, full_address: str):

        async with self.db_lock:
            # Проверяем существование записи
            async with self.db.execute("SELECT 1 FROM images WHERE user_id=?", (user_id,)) as cursor:
                exists = await cursor.fetchone()

            if exists:
                # Обновляем существующую запись
                await self.db.execute(
                    """UPDATE images 
                       SET latitude=?, longitude=?, full_address=?, updated_at=CURRENT_TIMESTAMP 
                       WHERE user_id=?""",
                    (latitude, longitude, full_address, user_id)
                )
            else:
                # Создаем новую запись
                await self.db.execute(
                    """INSERT INTO images (user_id, latitude, longitude, full_address, created_at) 
                       VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                    (user_id, latitude, longitude, full_address)
                )

            await self.db.commit()
            print(f"Геоданные сохранены для user_id={user_id}: {latitude}, {longitude}")


    async def select_user_id(self, user_id: int):
        async with self.db_lock:
            async with self.db.execute("SELECT * FROM images WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone()
