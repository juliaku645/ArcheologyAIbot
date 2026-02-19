import asyncio
import sqlite3
import os
from your_first_code import RAGImageSystem, Config
from your_second_code import GoskatalogParser  # если оформишь как класс


async def sync_all():
    # 1. Загружаем RAG систему
    rag = RAGImageSystem(Config())

    # 2. Берем все изображения из парсера, которых еще нет в RAG
    parser_db = sqlite3.connect("goskatalog.db")

    # Получаем хеши, которые уже есть в RAG
    rag_db = sqlite3.connect(rag.config.sqlite_db_path)
    existing = rag_db.execute("SELECT image_hash FROM images").fetchall()
    existing_hashes = {row[0] for row in existing}

    # Берем новые из парсера
    new_images = parser_db.execute(
        "SELECT image_path, description, image_hash FROM data"
    ).fetchall()

    # 3. Добавляем только новые
    added = 0
    for image_path, description, image_hash in new_images:
        if image_hash not in existing_hashes:
            with open(image_path, "rb") as f:
                image_bytes = f.read()
            await rag.add_image(image_bytes, description)
            added += 1
            print(f"➕ Добавлено: {image_hash}")

    print(f"\n✅ Синхронизация завершена! Добавлено {added} новых изображений")



if __name__ == "__main__":
    asyncio.run(sync_all())