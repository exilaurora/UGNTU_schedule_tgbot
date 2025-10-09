from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

class IsTodaySchedule(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        return message.text == "📅 Расписание на сегодня"