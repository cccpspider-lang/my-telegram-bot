import asyncio
import logging
from datetime import datetime

from aiogram import Bot

import database as db
from reminders.constants import ONE_TIME_REPEAT_TYPES
from utils.datetime_parser import next_occurrence

logger = logging.getLogger(__name__)
POLL_INTERVAL_SECONDS = 60


class ReminderService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self._poll_task: asyncio.Task | None = None

    async def process_due_reminders(self) -> None:
        due_tasks = db.get_due_tasks(datetime.now())

        for task in due_tasks:
            try:
                await self.bot.send_message(
                    chat_id=task["user_id"],
                    text=(
                        f"🔔 Напоминание о задаче #{task['task_number']}:\n"
                        f"{task['text']}"
                    ),
                )
                if task["repeat_type"] in ONE_TIME_REPEAT_TYPES:
                    db.clear_task_reminder(task["id"])
                else:
                    current = datetime.fromisoformat(task["remind_at"])
                    next_at = next_occurrence(current, task["repeat_type"])
                    db.reschedule_task(task["id"], next_at)
            except Exception:
                logger.exception(
                    "Не удалось отправить напоминание по задаче #%s пользователю %s",
                    task["id"],
                    task["user_id"],
                )

    async def _poll_loop(self) -> None:
        while True:
            try:
                await self.process_due_reminders()
            except Exception:
                logger.exception("Ошибка при проверке напоминаний")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def start_scheduler(self) -> None:
        if self._poll_task is None or self._poll_task.done():
            self._poll_task = asyncio.create_task(self._poll_loop())

    async def stop_scheduler(self) -> None:
        if self._poll_task is not None:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None
