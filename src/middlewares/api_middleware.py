from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Any, Awaitable, Callable, Dict

from rusoil_api import RusoilAPI


class RusoilAPIMiddleware(BaseMiddleware):
    """
    Middleware, которое автоматически добавляет RusoilAPI
    как аргумент в каждый хэндлер (если он его принимает).
    """

    def __init__(self, api: RusoilAPI):
        super().__init__()
        self.api = api

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        data["api"] = self.api  # 👈 теперь aiogram сможет передавать api=...
        return await handler(event, data)
