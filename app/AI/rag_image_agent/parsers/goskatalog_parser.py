import requests
import sqlite3
import os
import hashlib
from datetime import datetime


# =====================================================
# МИНИМАЛЬНЫЙ ПАРСЕР ГОСТАЛОГА (100 изображений)
# =====================================================

class GoskatalogParser:
    def __init__(self):
        # URL из рабочего примера
        self.EXHIBIT_URL = "https://goskatalog.ru/muzfo-rest/rest/exhibits/{}"
        self.IMAGE_URL = "https://goskatalog.ru/muzfo-imaginator/rest/images/public/150/{}/{}.jpg"

        self.HEADERS = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }

        # База данных
        self.DB_PATH = "goskatalog.db"
        self.IMAGE_DIR = "images"
        os.makedirs(self.IMAGE_DIR, exist_ok=True)

        # Счетчик
        self.collected = 0

        # Создаем таблицу
        with sqlite3.connect(self.DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data (
                    image_hash TEXT PRIMARY KEY,
                    image_path TEXT,
                    description TEXT
                )
            """)

    def get_image_hash(self, image_path):
        """MD5 хеш файла"""
        with open(image_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def process_one(self, object_id):
        """Обрабатывает один экспонат (как в твоем успешном примере)"""
        try:
            # Получаем описание
            resp = requests.get(self.EXHIBIT_URL.format(object_id), headers=self.HEADERS)
            data = resp.json()
            description = data.get("description", "").strip()

            # Получаем изображения
            for img in data.get("images", []):
                if self.collected >= 100:
                    return False

                image_id = img["id"]

                # Скачиваем
                img_url = self.IMAGE_URL.format(image_id, image_id)
                img_data = requests.get(img_url).content

                # Сохраняем
                image_path = os.path.join(self.IMAGE_DIR, f"{image_id}.jpg")
                with open(image_path, "wb") as f:
                    f.write(img_data)

                # Хеш и сохранение в БД
                image_hash = self.get_image_hash(image_path)

                with sqlite3.connect(self.DB_PATH) as conn:
                    conn.execute(
                        "INSERT OR IGNORE INTO data VALUES (?, ?, ?)",
                        (image_hash, image_path, description)
                    )

                self.collected += 1
                print(f"✅ {self.collected}/100: {image_id}")

            return True

        except Exception as e:
            print(f"❌ Ошибка с {object_id}: {e}")
            return True  # Продолжаем дальше

    def run(self, start_id=68220511, max_attempts=500):
        """Запуск парсинга до 100 изображений"""
        current_id = start_id

        while self.collected < 100 and current_id < start_id + max_attempts:
            print(f"\n🔍 Пробуем ID: {current_id}")
            should_continue = self.process_one(current_id)
            current_id += 1

            if not should_continue:
                break

        print(f"\n✅ Готово! Собрано {self.collected} изображений")


# =====================================================
# ЗАПУСК
# =====================================================

if __name__ == "__main__":
    parser = GoskatalogParser()
    parser.run()