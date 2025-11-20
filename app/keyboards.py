from aiogram.types import  InlineKeyboardMarkup, InlineKeyboardButton

keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Описание", callback_data="description"),
            InlineKeyboardButton(text="Добавить контекст", callback_data="add_context"),
            InlineKeyboardButton(text="Геоточка", callback_data="geo_point"),

        ]
    ])




