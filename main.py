import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import database as db
from config import BOT_TOKEN
from database import get_connection
from handlers import router
from reminders import init_reminders_table
from reminders.service import ReminderService
from services.context import set_reminder_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database() -> None:
    db.init_db()
    with get_connection() as conn:
        init_reminders_table(conn)
        conn.commit()


async def main() -> None:
    init_database()

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    reminder_service = ReminderService(bot)
    set_reminder_service(reminder_service)
    await reminder_service.start_scheduler()
    logger.info("Бот запущен. Напоминания активны.")

    try:
        await dp.start_polling(bot)
    finally:
        await reminder_service.stop_scheduler()


if __name__ == "__main__":
    asyncio.run(main())
