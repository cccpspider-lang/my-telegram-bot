import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import database as db
from config import BOT_TOKEN
from handlers import router
from reminders.service import ReminderService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    db.init_db()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    reminder_service = ReminderService(bot)
    await reminder_service.start_scheduler()
    logger.info("Бот запущен.")

    try:
        await dp.start_polling(bot)
    finally:
        await reminder_service.stop_scheduler()


if __name__ == "__main__":
    asyncio.run(main())
