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
    
    await message.answer(f"""Привет! Я помогу следить тебе за расписанием.
                         
Я буду работать даже если API УГНТУ недоступен, ведь я поддерживаю кэширование данных.

Я поддерживаю inline query. просто напиши {html.code('@ugntu_raspbot')} в любом чате.
Можно написать название группы, если нужно расписание другой группы.

Ты можешь отслеживать расписание сразу нескольких групп.
Достаточно запросить расписание, а затем сменить свою группу.
Сообщение, которое я отправлю после первого запроса будет актуально для той группы, которую ты запрашивал.

Даже при недоступности интернета ты не останешься без расписания, ведь telegram кэширует сообщения!

Начнем настройку!
""")

    await message.answer("Введи свою группу", reply_markup=ReplyKeyboardRemove())
    await state.set_state(UserState.waiting_for_group)