import os
import asyncio
from aiogram import Bot, Dispatcher, F, types, Router
from aiogram.filters import CommandStart
from dotenv import load_dotenv
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.AI.agent import get_description_for_image
from app.database import save_or_update_image, get_image_blob_from_db  #,init_db
import app.keyboards as kb
load_dotenv()



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
    # print(f'state = {state.get_state()}')



@router.message(
    Form.waiting_for_photo
)
async def handle_photo(message: types.Message, state: FSMContext, text=None):
    photo = message.photo[-1]
    file_id = photo.file_id
    user_id = message.from_user.id

    print(f'Пользователь {user_id} добавил ФОТО: {file_id}')


    file_info = await message.bot.get_file(photo.file_id)
    print(f'ФОТО: {file_id} получено')

    file_bytes_io = await message.bot.download_file(file_info.file_path)
    image_bytes = file_bytes_io.read()

    await save_or_update_image(user_id, text, image_bytes)
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
    image_bytes = await get_image_blob_from_db(user_id)
    print("Получена команда description, найдено изображение, идем в LLM")
    description = await get_description_for_image(image_bytes)
    await callback.message.answer(f"Описание фото:\n{description}")
    print(f"Описание фото:\n{description}")
    await callback.answer()

# @router.callback_query(F.data == 'add_context')
# async def add_context(callback:CallbackQuery):
#     user_id = callback.from_user.id  # Получаем user_id из callback
#     print(f"Получена команда add_context  от пользователя {user_id}")
#     message = await callback.message
#     await message.answer("Отправь мне дополнительный контекст")
#
#     print("Отправлено текстовое сообщение  пользователю")
#
#
#     print("Получено текстовое сообщение от пользователя")
#
#     await callback.answer()

    
async def main():

    dp = Dispatcher()

    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())
