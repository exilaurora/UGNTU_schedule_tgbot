import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery


class CooldownMiddleware(BaseMiddleware):
    def __init__(self, cooldown_seconds: float = 2.0):
        self.cooldown = cooldown_seconds
        self.last_calls: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Применяем кулдаун только к callback_query
        if isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
            if user_id is not None:
                now = time.monotonic()
                last = self.last_calls.get(user_id, 0.0)
                if now - last < self.cooldown:
                    # Сообщаем пользователю и останавливаем цепочку
                    await event.answer("⏳ Не так быстро пж", show_alert=False)
                    return None
                self.last_calls[user_id] = now

        # Иначе (или если кулдаун не сработал) — продолжаем обработку
        return await handler(event, data)
