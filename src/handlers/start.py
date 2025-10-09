from aiogram import Router, html, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from states.user_state import UserState

router = Router()

@router.message(CommandStart())
async def command_start(message: Message, state: FSMContext):
    user = message.from_user
    if not user:
        return

    await message.answer("Привет! Введи свою группу", reply_markup=ReplyKeyboardRemove())
    await state.set_state(UserState.waiting_for_group)