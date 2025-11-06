import os
import asyncio
from aiogram import Bot, Dispatcher, F, types, Router
from aiogram.filters import CommandStart
from dotenv import load_dotenv
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from app.AI.agent import get_description_for_image
from app.database import insert_image_to_db, get_image_blob_from_db  #,init_db
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

    await insert_image_to_db(user_id, text, image_bytes)
    print(f'ФОТО: {image_bytes} сохранено в БД')



    # keyboard = InlineKeyboardMarkup(inline_keyboard=[
    #     [
    #         InlineKeyboardButton(text="Описание", callback_data="description"),
    #         InlineKeyboardButton(text="Добавить контекст", callback_data="add_context"),
    #         InlineKeyboardButton(text="Геоточка", callback_data="geo_point"),
    #     ]
    # ])

    await state.set_state(Form.waiting_for_action)
    print("state = "+str(state))
    print("Отправляем ответное сообщение")
    await message.answer("Выберите действие:", reply_markup=kb.keyboard)
    print("Ответное сообщение отправлено")



@router.callback_query(F.data == 'description')

async def description(callback:CallbackQuery):
    print("Получена команда description, ищем изображение")
    image_bytes = await get_image_blob_from_db('1409137510')
    print("Получена команда description, найдено изображение, идем в LLM")
    description = await get_description_for_image(image_bytes)
    await callback.message.answer(f"Описание фото:\n{description}")
    print(f"Описание фото:\n{description}")
    await callback.answer()





#     elif action == "add_context":
#         await callback.message.answer("Отправьте дополнительный контекст к фото.")
#         await state.set_state(Form.waiting_for_context)
#
#     elif action == "geo_point":
#         await callback.message.answer("Пожалуйста, отправьте геоточку (местоположение).")
#
#
#     await callback.answer()
#
# @router.message(F.state == Form.waiting_for_context)
# async def handle_context(message: Message, state: FSMContext):
#     print(f'Получено waiting_for_context')
#     context = message.text
#     data = await state.get_data()
#     file_id = data.get("file_id")
#     user_id = message.from_user.id
#
#     # TODO: сохранить контекст в БД
#     # save_context_to_db(user_id, file_id, context_text)

    
async def main():
    #init_db()
    dp = Dispatcher()
    # get_image_from_db()
    # get_description_for_image()

    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())
