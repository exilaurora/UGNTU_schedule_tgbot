from aiogram import Router
from aiogram.types import Message
from rusoil_api import RusoilAPI

router = Router()

@router.message(lambda m: m.text and m.text.lower().startswith("сейчас"))
async def handle_now(message: Message, api: RusoilAPI):
    now = await api.get_now()
    await message.answer(f"Сегодня {now.day_of_week}-й день, неделя {now.week_number}.")
