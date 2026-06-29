from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

MOSCOW_TZ = ZoneInfo("Europe/Moscow")
MORNING_DIGEST_HOUR = 7


def now_moscow() -> datetime:
    """Текущее время в Москве (naive datetime для хранения в БД)."""
    return datetime.now(MOSCOW_TZ).replace(tzinfo=None)


def today_moscow() -> date:
    return now_moscow().date()


def tomorrow_moscow() -> date:
    return today_moscow() + timedelta(days=1)


def yesterday_moscow() -> date:
    return today_moscow() - timedelta(days=1)


def format_moscow_datetime(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")
