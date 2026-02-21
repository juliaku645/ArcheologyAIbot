'''import asyncio

import aiohttp


async def test():
    url = "https://goskatalog.ru/portal/#/collections?id=68180284"
    async with aiohttp.ClientSession() as session:
        try:
            print("Отправка запроса...")
            headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

            async with session.get(
                    url,
                    headers=headers,
                    timeout=30,  # 30 секунд, а не 30000
                    allow_redirects=True
            ) as response:
                print(f"Получен ответ: {response.status}")

                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '').lower()
                    print(f"Content-Type: {content_type}")

                    # Проверяем, что это HTML
                    if 'text/html' in content_type:
                        # ВАЖНО: нужно использовать await!
                        html = await response.text()
                        print(f"Длина HTML: {len(html)} символов")

                        # Выводим только часть HTML чтобы не засорять консоль
                        if len(html) > 500:
                            print("Первые 500 символов HTML:")
                            print(html[:500])
                        else:
                            print("Полный HTML:")
                            print(html)
                    else:
                        print(f"Пропускаем не-HTML контент: {url} ({content_type})")
                else:
                    print(f"HTTP {response.status} для {url}")

        except asyncio.TimeoutError:
            print(f"Таймаут при загрузке {url}")
        except Exception as e:
            print(f"Ошибка при загрузке {url}: {e}")


# Тест никиты
if __name__ == "__main__":
    print("Начало теста...")
    # Запускаем асинхронную функцию
    asyncio.run(test())

import requests
import sqlite3
import os
from datetime import datetime

# =====================================================
# НАСТРОЙКИ
# =====================================================

OBJECT_ID = 68220511

PAGE_URL = f"https://goskatalog.ru/portal/#/collections?id={OBJECT_ID}"
META_URL = f"https://goskatalog.ru/muzfo-rest/rest/exhibits/{OBJECT_ID}"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*"
}

DB_PATH = "artifacts.db"
IMAGE_DIR = "images"

os.makedirs(IMAGE_DIR, exist_ok=True)

# =====================================================
# SQL
# =====================================================

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id INTEGER,
    page_url TEXT,
    image_url TEXT,
    image_path TEXT,
    description TEXT,
    created_at TIMESTAMP
)
""")
conn.commit()

# =====================================================
# 1️⃣ ПОЛУЧАЕМ JSON ОПИСАНИЯ
# =====================================================

meta_response = requests.get(META_URL, headers=HEADERS, timeout=20)
meta_response.raise_for_status()
data = meta_response.json()

description = data.get("description", "").strip()

images = data.get("images", [])
if not images:
    raise RuntimeError("❌ У объекта нет изображений")

# берём первое изображение (обычно основное)
img = images[0]

image_id = img["id"]
size = img.get("size", 150)  # 150 — стандартный размер

# =====================================================
# 2️⃣ СТРОИМ ПРАВИЛЬНЫЙ URL ИЗОБРАЖЕНИЯ
# =====================================================

image_url = (
    f"https://goskatalog.ru/muzfo-imaginator/rest/images/public/"
    f"{size}/{image_id}/{image_id}.jpg"
)

# =====================================================
# 3️⃣ СКАЧИВАЕМ ИЗОБРАЖЕНИЕ
# =====================================================

img_response = requests.get(image_url, timeout=30)
img_response.raise_for_status()

image_path = os.path.join(IMAGE_DIR, f"{image_id}.jpg")

with open(image_path, "wb") as f:
    f.write(img_response.content)

# =====================================================
# 4️⃣ СОХРАНЯЕМ В SQL
# =====================================================

cursor.execute("""
INSERT INTO artifacts (
    object_id,
    page_url,
    image_url,
    image_path,
    description,
    created_at
)
VALUES (?, ?, ?, ?, ?, ?)
""", (
    OBJECT_ID,
    PAGE_URL,
    image_url,
    image_path,
    description,
    datetime.now()
))

conn.commit()
conn.close()

# =====================================================
# ГОТОВО
# =====================================================

print("✅ УСПЕХ")
print("ID объекта:", OBJECT_ID)
print("Изображение:", image_path)
print("URL изображения:", image_url
'''
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