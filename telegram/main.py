import os
import asyncio
from aiogram import Bot, Dispatcher, F, types, Router
from aiogram.filters import CommandStart
from dotenv import load_dotenv
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dadata import Dadata
from agent_proxy_service import get_description_for_image
from database import Database
import keyboards as kb
from keyboards import geo_keyboard
from aiogram.exceptions import TelegramBadRequest

from database import DATABASE_PATH

load_dotenv()
# DATABASE_PATH = "C:\\Users\\User\\ArcheologyAIbot\\images_blob.db"
database = Database(DATABASE_PATH)
DADATA_TOKEN = os.getenv("DADATA_TOKEN")

BOT_TOKEN = os.getenv("TG_TOKEN")
dadata = Dadata(DADATA_TOKEN)

print("TOKEN " + BOT_TOKEN)

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
    welcome_text = (
        "🤖 <b>ArcheologyAI</b> — ИИ-анализ археологических находок\n\n"
        
        "🔍 <b>Функции бота:</b>\n"
        "• <b>Получить описание</b> — бот создаст научное описание находки\n"
        "• <b>Отправить новое фото</b> — заменить текущее изображение\n"
        "• <b>Место раскопок</b> — добавить координаты места находки\n"
        "• <b>Добавить контекст</b> — прислать дополнительную информацию о находке\n\n"
        
        "📸 <b>Отправьте фото</b> для анализа\n\n"
        
        "✅ <b>Критерии для качественного фото:</b>\n"
        "• <b>Фон:</b> однотонный (белый/серый), без отвлекающих объектов\n"
        "• <b>Линейка:</b> рядом с находкой (реальная шкала в см)\n"
        "• <b>Освещение:</b> равномерное, без теней и бликов\n\n"
    )
    await message.answer(welcome_text, parse_mode="HTML")
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
    action_msg =await message.answer("Выберите действие:", reply_markup=kb.keyboard)
    print("Ответное сообщение отправлено")
    await state.update_data(action_message_id=action_msg.message_id)

@router.callback_query(F.data == 'description')
async def description(callback:CallbackQuery , state: FSMContext):
    user_id = callback.from_user.id  # Получаем user_id из callback
    data = await state.get_data()
    action_message_id = data.get('action_message_id')
    if action_message_id:
        try:
            await callback.message.bot.delete_message(callback.message.chat.id, action_message_id)
        except TelegramBadRequest:
            print("Не удалось удалить сообщение с действиями")
    print(f"Получена команда description от пользователя {user_id}, ищем изображение")
    image_bytes = await database.get_image_blob(user_id)
    if image_bytes is None:
        await callback.message.answer("Изображение не найдено в базе данных.")
        await state.clear()
        return

    context_text = await database.get_context(user_id)
    # Вызываем функцию генерации описания с фото и контекстом
    description = await get_description_for_image(image_bytes, context_text)
    print(f"Описание для пользователя {user_id}: {description}")
    await callback.message.answer(f"Описание фото :\n{description}")
    # сохраняем в БД ответ
    await database.save_description(user_id,context_text,image_bytes, description)
    print("Данные сохранены в БД")
    await callback.message.answer('Описание фото составлено. Теперь вы можете отправить новую фотографию для описания, нажав кнопку ниже ',reply_markup=kb.keyboard1)
    print("Сообщение отправлено пользователю")
    await state.set_state(Form.waiting_for_action)
    await callback.answer()


@router.callback_query(F.data =="send_photo")
async def send_photo(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    action_msg_id = data.get('action_message_id')
    if action_msg_id:
        try:
            await callback.message.bot.delete_message(callback.message.chat.id, action_msg_id)
        except TelegramBadRequest:
            pass
    print(f"Получена команда add_context от пользователя {user_id}")
    await callback.message.answer("Отправьте новое фото")
    await state.set_state(Form.waiting_for_photo)
    await callback.answer()


@router.callback_query(F.data == 'add_context')
async def add_context(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = await state.get_data()
    action_msg_id = data.get('action_message_id')
    if action_msg_id:
        try:
            await callback.message.bot.delete_message(callback.message.chat.id, action_msg_id)
        except TelegramBadRequest:
            pass
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
    print("Контекст сохранён")
    await state.set_state(Form.waiting_for_action)
    await message.answer("Контекст сохранен!",
         reply_markup=kb.keyboard)
    print("Ответное сообщение отправлено")
    await state.clear()

@router.callback_query(F.data == 'geo_point')
async def geo_point(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    print(f"Получена команда от пользователя {user_id}")
    data = await state.get_data()
    action_msg_id = data.get('action_message_id')
    if action_msg_id:
        try:
            await callback.message.bot.delete_message(callback.message.chat.id, action_msg_id)
        except TelegramBadRequest:
            pass
    await callback.message.answer("Отправьте место обнаружения находки", reply_markup=kb.geo_keyboard)
    print("Пользователь отправил геоточку")
    await state.set_state(Form.waiting_for_geo)
    await callback.answer()


@router.message(Form.waiting_for_geo, F.location)
async def process_geo(message: Message, state: FSMContext):
    latitude = float(message.location.latitude)
    longitude = float(message.location.longitude)
    user_id = message.from_user.id


    # Получаем адрес через DaData
    try:
        result = dadata.geolocate(name="address", lat=latitude, lon=longitude)
        if result and len(result) > 0:
            address = result[0]['data']['address']
            full_address = f"{address.get('city', '')}, {address.get('street', '')} {address.get('house', '')}".strip(
                ', ')
        else:
            full_address = "Адрес не определен"
    except Exception as e:
        print(f"Ошибка DaData: {e}")
        full_address = "Не удалось определить адрес"

    await database.save_geo_with_address(user_id, latitude, longitude, full_address)
    # Формируем ответ с координатами и адресом
    action_msg = await message.answer(

   f"📍 Адрес: {full_address}\n"
        f"📊 Координаты:\n"
        f"Широта: {latitude:.6f}\n"
        f"Долгота: {longitude:.6f}",
        reply_markup=kb.keyboard
    )


    await state.update_data(action_message_id=action_msg.message_id)
    await state.clear()



async def test_agent():

    user_id = database.select_user_id()
    image_bytes = await database.get_image_blob(user_id)  # await важен
    user_context = await database.get_context(user_id)
    if image_bytes is None:
        print("Изображение не найдено в базе данных")
        return
    description = await get_description_for_image(image_bytes,user_context)
    print(description)
     # Сохраняем текст описания в БД

# if __name__ == "__main__":
#     asyncio.run(test_agent())
# #



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



