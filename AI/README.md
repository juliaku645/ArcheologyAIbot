# AI Модуль для анализа изображений

Этот модуль предоставляет функционал для анализа изображений археологических артефактов с использованием RAG (Retrieval-Augmented Generation) системы.

## Структура модуля

- **`agent.py`** - Основной класс `Agent` с методом `get_description_for_image`
- **`database.py`** - Модуль для работы с SQLite базой данных (хранение описаний изображений)
- **`vector_db.py`** - Модуль для работы с векторной БД FAISS (хранение изображений)
- **`goskatalog_parser.py`** - Парсер для выгрузки данных с сайта goskatalog.ru
- **`run_parser.py`** - Скрипт для запуска парсера

## Функционал

### 1. Выгрузка данных из goskatalog

Парсер `GoskatalogParser` позволяет загружать данные с сайта goskatalog.ru:
- Получает описания экспонатов
- Скачивает изображения
- Сохраняет описания в SQLite
- Сохраняет изображения в векторной БД FAISS

Запуск парсера:
```python
python AI/run_parser.py
```

### 2. Хранение данных

- **SQLite** (`databases/images_metadata.db`) - хранит описания изображений с их хешами
- **FAISS** (`databases/faiss`) - хранит векторные представления изображений

### 3. Метод `get_description_for_image`

Метод выполняет следующую цепочку действий:

1. **Поиск похожих изображений**: По входному изображению в векторной БД FAISS находятся 3 наиболее похожих изображения
2. **Получение описаний**: По хешам найденных изображений в SQLite БД извлекаются их описания
3. **Анализ LLM**: Собранная информация (описания похожих изображений + пользовательский контекст) отправляется в LLM для определения того, что находится на первоначальном изображении

#### Использование:

```python
from AI.agent import get_description_for_image
import asyncio

async def main():
    # Загружаем изображение
    with open("image.jpg", "rb") as f:
        image_bytes = f.read()
    
    # Получаем описание
    description = await get_description_for_image(
        image_bytes=image_bytes,
        user_context="Это археологический артефакт"
    )
    print(description)

asyncio.run(main())
```

## Зависимости

Убедитесь, что установлены следующие пакеты:

```
langchain-openai
sentence-transformers
faiss-cpu (или faiss-gpu)
aiosqlite
Pillow
numpy
requests
python-dotenv
```

## Конфигурация

Настройки выполняются через переменные окружения в файле `.env`:

- `OPENAI_API_KEY` - API ключ OpenAI
- `MODEL_NAME` - Название модели (по умолчанию "gpt-4o")
- `SYSTEM_PROMPT` - Системный промпт для LLM
- `IS_TEST` - Режим тестирования (True/False)

## Структура базы данных

### SQLite (images_metadata.db)

Таблица `images`:
- `image_hash` (TEXT, PRIMARY KEY) - MD5 хеш изображения
- `description` (TEXT) - Описание изображения
- `faiss_index_id` (INTEGER) - ID в FAISS индексе

### FAISS

- `faiss_index.bin` - Индекс FAISS
- `faiss_metadata.npy` - Метаданные (хеши изображений)
