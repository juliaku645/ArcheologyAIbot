"""
Модуль для работы с SQLite базой данных для хранения описаний изображений.
"""
import aiosqlite
import os
from typing import Optional, List


class ImageDatabase:
    """Класс для работы с SQLite базой данных изображений."""
    
    def __init__(self, db_path: str = "AI/database/images_metadata.db"):
        """
        Инициализация базы данных.
        
        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = db_path
        # Создаем директорию, если её нет
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    async def init_db(self):
        """Инициализация таблицы в базе данных."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    image_hash TEXT PRIMARY KEY,
                    description TEXT,
                    faiss_index_id INTEGER
                )
            """)
            await db.commit()
    
    async def add_image(self, image_hash: str, description: str, faiss_index_id: int):
        """
        Добавить изображение в базу данных.
        
        Args:
            image_hash: MD5 хеш изображения
            description: Описание изображения
            faiss_index_id: ID в FAISS индексе
        """
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO images (image_hash, description, faiss_index_id) VALUES (?, ?, ?)",
                (image_hash, description, faiss_index_id)
            )
            await db.commit()
    
    async def get_description_by_hash(self, image_hash: str) -> Optional[str]:
        """
        Получить описание изображения по его хешу.
        
        Args:
            image_hash: MD5 хеш изображения
            
        Returns:
            Описание изображения или None, если не найдено
        """
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT description FROM images WHERE image_hash = ?",
                (image_hash,)
            )
            row = await cursor.fetchone()
            return row[0] if row and row[0] else None
    
    async def get_descriptions_by_hashes(self, image_hashes: List[str]) -> List[str]:
        """
        Получить описания изображений по их хешам.
        
        Args:
            image_hashes: Список MD5 хешей изображений
            
        Returns:
            Список описаний (только непустые)
        """
        await self.init_db()
        descriptions = []
        async with aiosqlite.connect(self.db_path) as db:
            for image_hash in image_hashes:
                cursor = await db.execute(
                    "SELECT description FROM images WHERE image_hash = ?",
                    (image_hash,)
                )
                row = await cursor.fetchone()
                if row and row[0]:
                    descriptions.append(row[0])
        return descriptions
    
    async def image_exists(self, image_hash: str) -> bool:
        """
        Проверить, существует ли изображение в базе данных.
        
        Args:
            image_hash: MD5 хеш изображения
            
        Returns:
            True, если изображение существует, иначе False
        """
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM images WHERE image_hash = ?",
                (image_hash,)
            )
            return await cursor.fetchone() is not None
    
    async def get_stats(self) -> dict:
        """
        Получить статистику базы данных.
        
        Returns:
            Словарь со статистикой
        """
        await self.init_db()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM images")
            count = (await cursor.fetchone())[0]
            return {"images": count}
