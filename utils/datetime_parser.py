import calendar
import re
from datetime import datetime, timedelta


def parse_time_only(value: str, now: datetime | None = None) -> datetime | None:
    """Парсит время HH:MM для сегодня или завтра, если время уже прошло."""
    now = now or datetime.now()
    value = value.strip()

    match = re.fullmatch(r"(\d{1,2})[:.](\d{2})", value)
    if not match:
        return None

    hour, minute = int(match.group(1)), int(match.group(2))
    if hour > 23 or minute > 59:
        return None

    remind_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if remind_at <= now:
        remind_at += timedelta(days=1)

    return remind_at


def parse_date_time(value: str, now: datetime | None = None) -> datetime | None:
    """Парсит дату и время: DD.MM.YYYY HH:MM или DD.MM HH:MM."""
    now = now or datetime.now()
    value = value.strip()

    patterns = [
        (r"(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2})[:.](\d{2})", True),
        (r"(\d{1,2})\.(\d{1,2})\s+(\d{1,2})[:.](\d{2})", False),
    ]

    for pattern, has_year in patterns:
        match = re.fullmatch(pattern, value)
        if not match:
            continue

        if has_year:
            day, month, year, hour, minute = map(int, match.groups())
        else:
            day, month, hour, minute = map(int, match.groups())
            year = now.year

        if not (1 <= day <= 31 and 1 <= month <= 12 and 0 <= hour <= 23 and 0 <= minute <= 59):
            return None

        try:
            remind_at = datetime(year, month, day, hour, minute)
        except ValueError:
            return None

        if remind_at <= now:
            return None

        return remind_at

    return None


def parse_strict_date_time(value: str, now: datetime | None = None) -> datetime | None:
    """Строгий формат: DD.MM.YYYY HH:MM."""
    now = now or datetime.now()
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

    if remind_at <= now:
        return None

    return remind_at


def format_remind_at(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")


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
