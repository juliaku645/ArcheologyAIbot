import os
import asyncio
from aiogram import Bot, Dispatcher, F, types, Router
from aiogram.filters import CommandStart
from dotenv import load_dotenv
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.AI.agent import get_description_for_image
from app.database import Database
import app.keyboards as kb
load_dotenv()
DATABASE_PATH = "C:\\Users\\User\\ArcheologyAIbot\\images_blob.db"
database = Database(DATABASE_PATH)


BOT_TOKEN = os.getenv("TG_TOKEN")


bot = Bot(token=BOT_TOKEN)
router = Router()



class Form(StatesGroup):
    waiting_for_photo = State()
    waiting_for_action = State()
    waiting_for_description = State()
    waiting_for_context = State()
    waiting_for_geo = State()

@router.message(CommandStart())
async def cmd_start(message: Message,state: FSMContext):
    await message.answer("Привет! Отправь мне сообщение с картинкой")
    await state.set_state(Form.waiting_for_photo)



@router.message(
    Form.waiting_for_photo
)
async def handle_photo(message: types.Message, state: FSMContext, context=None):
    photo = message.photo[-1]
    file_id = photo.file_id
    user_id = message.from_user.id

    print(f'Пользователь {user_id} добавил ФОТО: {file_id}')


    file_info = await message.bot.get_file(photo.file_id)
    print(f'ФОТО: {file_id} получено')

    file_bytes_io = await message.bot.download_file(file_info.file_path)
    image_bytes = file_bytes_io.read()

    await database.save_or_update_image(user_id, image_bytes, context)
    print(f'ФОТО сохранено в БД')

    await state.set_state(Form.waiting_for_action)
    print("state = "+str(state))
    print("Отправляем ответное сообщение")
    await message.answer("Выберите действие:", reply_markup=kb.keyboard)
    print("Ответное сообщение отправлено")


@router.callback_query(F.data == 'description')

async def description(callback:CallbackQuery):
    user_id = callback.from_user.id  # Получаем user_id из callback
    print(f"Получена команда description от пользователя {user_id}, ищем изображение")
    image_bytes = await database.get_image_blob(user_id)
    
    if image_bytes is None:
        await callback.message.answer("Изображение для вашего user_id не найдено в базе данных.")
    else:
        description = await get_description_for_image(image_bytes)

        await callback.message.answer(f"Описание фото:\n{description}")
    await callback.answer()



@router.callback_query(F.data == 'add_context')
async def add_context(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    print(f"Получена команда add_context от пользователя {user_id}")
    await callback.message.answer("Отправь мне дополнительный контекст")
    await state.set_state(Form.waiting_for_context)
    await callback.answer()

@router.message(Form.waiting_for_context)
async def process_context(message: Message, state: FSMContext):
    user_id = message.from_user.id
    context_text = message.text
    print(f"Получено текстовое сообщение от пользователя {user_id}: {context_text}")
    await database.update_text(user_id, context_text)  # Сохраняем контекст в базе
    await message.answer("Контекст сохранён")
    image_bytes = await database.get_image_blob(user_id)
    if image_bytes is None:
        await message.answer("Изображение не найдено в базе данных.")
        await state.clear()
        return

        # Вызываем функцию генерации описания с фото и контекстом
    description = await get_description_for_image(image_bytes, context_text)
    print(f"Описание для пользователя {user_id}: {description}")
    await message.answer(f"Описание фото с учётом контекста:\n{description}")

    await state.clear()


    
async def main():
    await database.connect()  # одно подключение при старте бота

    dp = Dispatcher()
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await database.close()  # корректное закрытие подключения при завершении

if __name__ == "__main__":

    asyncio.run(main())
