import logging

from aiogram import Router, F

from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from rusoil_api import RusoilAPI

from filters.admin import Admin

router = Router()

repairKeyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отменить", callback_data="BreakAPI:cancel")]
])


@router.message(Command(commands=["BreakAPI"]), Admin())
async def HandleAPIErrorCommand(message: Message, api: RusoilAPI):
    api.BASE_URL = "https://example.com" # pyright: ignore[reportAttributeAccessIssue]
    logging.info("Активирована симуляция недоступности API")
    await message.reply("Активирована симуляция недоступности API", reply_markup=repairKeyboard)


@router.callback_query(F.data == ("BreakAPI:cancel"))
async def HandleAPIRepairQuery(callback: CallbackQuery, api: RusoilAPI):
    api.BASE_URL = RusoilAPI.BASE_URL
    logging.info("Симуляция недоступности API отключена")
    await callback.answer()
    if (message:= callback.message) and isinstance(message, Message):
        await message.delete()