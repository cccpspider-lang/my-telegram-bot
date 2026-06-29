import asyncio
import logging

from aiogram import Bot

import database as db
from digest.formatters import format_morning_plan
from digest.stats import get_completed_yesterday, get_productivity_streak
from utils.timezone import MORNING_DIGEST_HOUR, now_moscow, today_moscow

logger = logging.getLogger(__name__)
POLL_INTERVAL_SECONDS = 60


class MorningDigestService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self._poll_task: asyncio.Task | None = None

    async def process_morning_digests(self) -> None:
        now = now_moscow()
        if now.hour < MORNING_DIGEST_HOUR:
            return

        logger.info("Morning digest started")
        today_str = today_moscow().isoformat()

        for user in db.get_all_users():
            user_id = user["user_id"]
            if db.was_morning_digest_sent(user_id, today_str):
                continue

            logger.info("Sending morning plan to user %s", user_id)
            try:
                name = user["first_name"] or "друг"
                tasks = db.get_today_tasks(user_id, today_str)
                total_today = len(tasks)
                completed_yesterday = get_completed_yesterday(user_id)
                streak = get_productivity_streak(user_id)
                text = format_morning_plan(
                    name,
                    tasks,
                    total_today,
                    completed_yesterday,
                    streak,
                )
                await self.bot.send_message(chat_id=user_id, text=text)
                db.mark_morning_digest_sent(user_id, today_str)
                logger.info("Morning plan sent successfully")
            except Exception:
                logger.exception(
                    "Не удалось отправить утренний план пользователю %s",
                    user_id,
                )

    async def _poll_loop(self) -> None:
        while True:
            try:
                await self.process_morning_digests()
            except Exception:
                logger.exception("Ошибка при отправке утреннего плана")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def start_scheduler(self) -> None:
        if self._poll_task is None or self._poll_task.done():
            self._poll_task = asyncio.create_task(self._poll_loop())
            logger.info(
                "Morning digest scheduler started (interval: %ss, timezone: Europe/Moscow)",
                POLL_INTERVAL_SECONDS,
            )

    async def stop_scheduler(self) -> None:
        if self._poll_task is not None:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None
