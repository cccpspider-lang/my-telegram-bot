import asyncio
import logging
from datetime import datetime

from aiogram import Bot

from reminders import repository as reminder_repo
from reminders.constants import REPEAT_ONCE
from utils.datetime_parser import next_occurrence

logger = logging.getLogger(__name__)
POLL_INTERVAL_SECONDS = 60


class ReminderService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self._poll_task: asyncio.Task | None = None

    async def schedule(
        self,
        user_id: int,
        message: str,
        remind_at: datetime,
        task_id: int | None = None,
        repeat_type: str = REPEAT_ONCE,
    ) -> tuple[int, int | None]:
        return reminder_repo.create_reminder(
            user_id=user_id,
            message=message,
            remind_at=remind_at,
            task_id=task_id,
            repeat_type=repeat_type,
        )

    async def process_due_reminders(self) -> None:
        due_reminders = reminder_repo.get_pending_reminders(datetime.now())

        for reminder in due_reminders:
            try:
                await self.bot.send_message(
                    chat_id=reminder["user_id"],
                    text=f"🔔 Напоминание:\n{reminder['message']}",
                )
                if reminder["repeat_type"] == REPEAT_ONCE:
                    reminder_repo.delete_reminder_by_id(reminder["id"])
                else:
                    current = datetime.fromisoformat(reminder["remind_at"])
                    next_at = next_occurrence(current, reminder["repeat_type"])
                    reminder_repo.reschedule_reminder(reminder["id"], next_at)
            except Exception:
                logger.exception(
                    "Не удалось отправить напоминание #%s пользователю %s",
                    reminder["id"],
                    reminder["user_id"],
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
