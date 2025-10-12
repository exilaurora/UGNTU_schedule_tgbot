import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.mongo import MongoStorage
from motor.motor_asyncio import AsyncIOMotorClient

from rusoil_api.rusoil_cachingapi import RusoilSafeAPI
from middlewares.api_middleware import RusoilAPIMiddleware
from middlewares.cooldown_middleware import CooldownMiddleware
from handlers import register_handlers

TOKEN = getenv("BOT_TOKEN")

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    mongo_uri = (
        f"mongodb://{getenv('MONGO_USER')}:{getenv('MONGO_PASSWORD')}"
        f"@{getenv('MONGO_HOST')}:{getenv('MONGO_PORT')}/{getenv('MONGO_DB')}"
    )

    if not TOKEN:
        raise RuntimeError("BOT_TOKEN не установлен в окружении")

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    client = AsyncIOMotorClient(mongo_uri)

    storage = MongoStorage(client=client, db_name="mydatabase")
    dp = Dispatcher(storage=storage)

    api = RusoilSafeAPI()
    await api.__aenter__()

    dp.update.middleware(RusoilAPIMiddleware(api))
    dp.callback_query.middleware(CooldownMiddleware(1))


    register_handlers(dp)

    try:
        await dp.start_polling(bot)
    finally:
        await api.__aexit__(None, None, None)
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
