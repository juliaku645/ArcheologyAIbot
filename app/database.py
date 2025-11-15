import aiosqlite
import asyncio
DATABASE_PATH = "C:\\Users\\User\\ArcheologyAIbot\\images_blob.db"
db_lock = asyncio.Lock()
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

    async def save_or_update_image(self, user_id: int, text: str, image_bytes: bytes):
        async with self.db_lock:
            async with self.db.execute("SELECT 1 FROM images WHERE user_id=?", (user_id,)) as cursor:
                exists = await cursor.fetchone()
            if exists:
                await self.db.execute("UPDATE images SET photo=?, text=? WHERE user_id=?", (image_bytes, text, user_id))
            else:
                await self.db.execute("INSERT INTO images (user_id, text, photo) VALUES (?, ?, ?)", (user_id, text, image_bytes))
            await self.db.commit()

    async def select_user_id(self, user_id: int):
        async with self.db_lock:
            async with self.db.execute("SELECT * FROM images WHERE user_id=?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row

    async def get_image_blob(self, user_id: int):
        # Чтение можно опционально не блокировать, но для безопасности можно сделать с lock
        async with self.db_lock:
            async with self.db.execute("SELECT photo FROM images WHERE user_id=?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0]
                return None

