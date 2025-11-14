# import asyncio
# from aiogram import Router, F
# from aiogram.enums import ChatAction
# from aiogram.types import Message
# from aiogram.filters import CommandStart, Command
#
# import app.keyboards as keyboard
#
# router=Router()
#
#
#
# @router.message(F.photo)
# async def handle_photo(message: Message):
#     photo_sizes = message.photo
#     file_id = photo_sizes[-1].file_id
#     await message.answer("Выберите действие:", reply_markup = keyboard)



