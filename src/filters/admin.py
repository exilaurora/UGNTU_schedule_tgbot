from os import getenv

from aiogram.filters import BaseFilter
from aiogram.types import Message

admin = getenv("ADMIN_USERID")
class Admin(BaseFilter):
    async def __call__(self, message: Message):
        if not admin or not message.from_user:
            return False
        return str(message.from_user.id) == admin