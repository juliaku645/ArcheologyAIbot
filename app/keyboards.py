from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


# inline_main = InlineKeyboardMarkup(inline_keyboard=[
#     [InlineKeyboardButton(text='Корзина', callback_data='basket')],
#     [InlineKeyboardButton(text='Каталог', callback_data='catalog')],
#     [InlineKeyboardButton(text='Контакты', callback_data='contacts')]
# ])

main= ReplyKeyboardMarkup(keyboard=[
         [KeyboardButton(text='Меню'),
          KeyboardButton(text='Корзина')],
         [KeyboardButton(text='Контакты')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт ниже'
)