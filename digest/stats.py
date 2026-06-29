from datetime import timedelta

import database as db
from utils.timezone import today_moscow, yesterday_moscow


def get_completed_yesterday(user_id: int) -> int:
    return db.count_completed_on_date(user_id, yesterday_moscow().isoformat())


def get_productivity_streak(user_id: int) -> int:
    completion_dates = set(db.get_completion_dates(user_id))
    if not completion_dates:
        return 0

    current = today_moscow()
    if current.isoformat() not in completion_dates:
        current = yesterday_moscow()

    streak = 0
    while current.isoformat() in completion_dates:
        streak += 1
        current -= timedelta(days=1)

    return streak
