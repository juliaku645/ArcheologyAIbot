import aiosqlite
import asyncio
DATABASE_PATH = "C:\\Users\\User\\ArcheologyAIbot\\images_blob.db"
db_lock = asyncio.Lock()
class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.db = None

    async def connect(self):
        self.db = await aiosqlite.connect(self.db_path, timeout=30)
        await self.db.execute("PRAGMA journal_mode=WAL")  # Установка WAL для лучшей параллельности
        await self.db.commit()

    async def close(self):
        await self.db.close()

# Метод общается в БД и ищет строку, в которой user_id = заданному (SELECT * FROM images WHERE user_id = ?)

# Если строка нашлась - выполняем UPDATE images set photo = ? where user_id = ?
# Если строка не нашлась - выполняем INSERT INTO images (user_id, text, photo) VALUES (?,
async def save_or_update_image(user_id: int, text : str, image_bytes: bytes):
    async with db_lock:
        async with aiosqlite.connect(DATABASE_PATH,timeout=10) as db:
            async with db.execute("SELECT 1 FROM images WHERE user_id=?", (user_id,)) as cursor:
                exists = await cursor.fetchone()

            if exists:
                await db.execute("UPDATE images SET photo=?, text =? WHERE user_id=?", (image_bytes,text, user_id))
            else:
            # Если нет, вставляем новую строку
                await db.execute(
                "INSERT INTO images (user_id, text, photo) VALUES (?, ?, ?)",
                (user_id, text, image_bytes)
            )

            await db.commit()

async def select_user_id(user_id: int):
    async with db_lock:
        async with aiosqlite.connect(DATABASE_PATH,timeout=10) as db:
            async with db.execute("SELECT * FROM images WHERE user_id=?", (user_id,)) as cursor:
                cursor = await cursor.fetchone()
                return cursor

async def get_image_blob_from_db(user_id: int):
    async with aiosqlite.connect(DATABASE_PATH,timeout=10) as db:
        async with db.execute("SELECT photo FROM images WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return row[0]
async def main():
    database = Database(DATABASE_PATH)
    await database.connect()
    await database.close()
