"""
Скрипт для запуска парсера данных с сайта goskatalog.ru.
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from AI.database import ImageDatabase
from AI.vector_db import VectorDatabase
from AI.goskatalog_parser import GoskatalogParser


async def main():
    """Основная функция для запуска парсера."""
    print("🚀 Инициализация компонентов...")
    
    # Инициализируем базы данных
    db = ImageDatabase()
    vector_db = VectorDatabase()
    
    # Инициализируем парсер
    parser = GoskatalogParser(db=db, vector_db=vector_db)
    
    # Запускаем парсинг
    # Параметры:
    # - start_id: начальный ID экспоната (по умолчанию 68220511)
    # - max_images: максимальное количество изображений для сбора (по умолчанию 100)
    # - max_attempts: максимальное количество попыток (по умолчанию 500)
    await parser.run(
        start_id=68220511,
        max_images=100,
        max_attempts=500
    )
    
    # Выводим статистику
    db_stats = await db.get_stats()
    vector_stats = vector_db.get_stats()
    print(f"\n📊 Статистика:")
    print(f"   SQLite: {db_stats['images']} изображений")
    print(f"   FAISS: {vector_stats['vectors']} векторов")


if __name__ == "__main__":
    asyncio.run(main())
