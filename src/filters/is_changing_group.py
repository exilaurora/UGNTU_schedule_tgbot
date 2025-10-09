from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

class IsChangingGroup(BaseFilter):
    async def __call__(self, message: Message, state: FSMContext) -> bool:
        return message.text == "🔄 Сменить группу"