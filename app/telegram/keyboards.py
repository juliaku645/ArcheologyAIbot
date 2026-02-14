from aiogram.types import  InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Получить \n описание", callback_data="description"),
            InlineKeyboardButton(text="Добавить \n контекст", callback_data="add_context"),
            InlineKeyboardButton(text="Место \n раскопок", callback_data="geo_point"),

        ]
    ])
keyboard1 = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Отправить новое фото", callback_data="send_photo")
    ]
])
geo_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


