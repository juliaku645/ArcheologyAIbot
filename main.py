import os
import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv

load_dotenv()



BOT_TOKEN = os.getenv("TG_TOKEN")
DATABASE_PATH = "images_blob.db"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def init_db():
    # Инициализация базы данных с таблицей для хранения BLOB
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT,
            photo BLOB
        )
    """)
    conn.commit()
    conn.close()

def convert_file_to_binary(filename: str) -> bytes:
    # Чтение файла в бинарном режиме
    with open(filename, 'rb') as file:
        blob_data = file.read()
    return blob_data

def insert_image_to_db(user_id: int, text: str, photo_path: str):
    # Вставка бинарных данных изображения в БД
    blob_data = convert_file_to_binary(photo_path)
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO images (user_id, text, photo) VALUES (?, ?, ?)",
        (user_id, text, blob_data)
    )
    conn.commit()
    conn.close()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Отправь мне сообщение с картинкой и текстом, "
        "я сохраню их в базу как BLOB."
    )

@dp.message(F.content_type == types.ContentType.PHOTO)
async def handle_photo_message(message: types.Message):
    text = message.caption or ""
    user_id = message.from_user.id

    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_ext = os.path.splitext(file_info.file_path)[1]
    filename = f"{photo.file_id}{file_ext}"
    tmp_filepath = f"temp_{filename}"

    #  скачиваем файл во временное хранилище
    await bot.download_file(file_info.file_path, destination=tmp_filepath)

    # Сохраняем бинарные данные изображения в БД
    insert_image_to_db(user_id, text, tmp_filepath)

    # Удаляем временный файл после сохранения
    os.remove(tmp_filepath)



    def get_image_and_text_from_db(record_id: int):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT text, photo FROM images WHERE id=?", (record_id,))
        result = cursor.fetchone()
        conn.close()
        return result  # (text, blob)

    async def send_to_llm(text: str, image_path: str):
        """Заглушка функции отправки текста и изображения в LLM API"""
        # Здесь реализация отправки в API LLM, например через HTTP запрос
        # image_path - путь к изображению, текст - описание/подпись
        print("Отправка в LLM:", text, image_path)
        await asyncio.sleep(1)  # эмуляция задержки
        return "Ответ LLM: Обработано успешно"

    @dp.message(Command(commands=["process"]))
    async def process_message(message:types.Message):
        args = message.get_args()
        if not args.isdigit():
            await message.answer("Пожалуйста, укажите корректный ID записи после команды")
            return

        record_id = int(args)
        data = get_image_and_text_from_db(record_id)
        if data is None:
            await message.answer(f"Запись с ID {record_id} не найдена.")
            return

        text, blob = data
        temp_image_path = f"temp_download_{record_id}.jpg"
        with open(temp_image_path, 'wb') as f:
            f.write(blob)

        llm_response = await send_to_llm(text, temp_image_path)
        os.remove(temp_image_path)

        await message.answer(llm_response)
    await message.answer("Изображение и текст сохранены в базе данных в формате BLOB!")
async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
