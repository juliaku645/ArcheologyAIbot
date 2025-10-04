import asyncio
from aiogram import Router, F
from aiogram.enums import ChatAction
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

import app.keyboards as kb

router=Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.bot.send_chat_action(chat_id=message.from_user.id, action=ChatAction.TYPING)
    await asyncio.sleep(2)
    await message.answer(text='Привет!Чем могу помочь?', reply_markup = kb.main)


@router.message(Command('help'))
async def cmd_help(message:Message):
    await message.bot.send_chat_action(chat_id=message.from_user.id, action=ChatAction.TYPING)
    await asyncio.sleep(2)
    await message.answer('Помощь')

@router.message(F.photo)
async def handle_photo(message:Message):
    file_id = message.photo[-1].file_id
    await message.answer_photo(file_id, caption='Вот твое фото')

@router.message(F.text=='проверка роутера')
async def check_router(message:Message):
    await message.answer('Ok')

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(f'Привет!', reply_markup=kb.inline_main)
