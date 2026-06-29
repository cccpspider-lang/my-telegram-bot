import calendar
import re
from datetime import date, datetime, timedelta

from utils.timezone import now_moscow


def parse_moscow_time(value: str, target_date: date) -> datetime | None:
    """Парсит время HH:MM для указанной даты по Москве."""
    value = value.strip()
    match = re.fullmatch(r"(\d{1,2})[:.](\d{2})", value)
    if not match:
        return None

    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        return None

    try:
        remind_at = datetime(target_date.year, target_date.month, target_date.day, hour, minute)
    except ValueError:
        return None

    if remind_at <= now_moscow():
        return None

    return remind_at


def parse_strict_date_time(value: str) -> datetime | None:
    """Строгий формат: DD.MM.YYYY HH:MM (московское время)."""
    value = value.strip()
    match = re.fullmatch(
        r"(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2})[:.](\d{2})",
        value,
    )
    if not match:
        return None

    day, month, year, hour, minute = map(int, match.groups())
    if not (1 <= day <= 31 and 1 <= month <= 12 and 0 <= hour <= 23 and 0 <= minute <= 59):
        return None

    try:
        remind_at = datetime(year, month, day, hour, minute)
    except ValueError:
        return None

    if remind_at <= now_moscow():
        return None

    return remind_at


def format_remind_at(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M") + " МСК"


def next_occurrence(current: datetime, repeat_type: str) -> datetime:
    if repeat_type == "daily":
        return current + timedelta(days=1)

    if repeat_type == "weekly":
        return current + timedelta(weeks=1)

    if repeat_type == "monthly":
        month = current.month + 1
        year = current.year
        if month > 12:
            month = 1
            year += 1
        day = min(current.day, calendar.monthrange(year, month)[1])
        return current.replace(year=year, month=month, day=day)

    return current
