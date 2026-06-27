import sqlite3
from datetime import datetime

from database import get_connection


def init_reminders_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_id INTEGER,
            message TEXT NOT NULL,
            remind_at TIMESTAMP NOT NULL,
            is_sent INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE SET NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders (user_id)"
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reminders_due
        ON reminders (is_sent, remind_at)
        """
    )


def create_reminder(
    user_id: int,
    message: str,
    remind_at: datetime,
    task_id: int | None = None,
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO reminders (user_id, task_id, message, remind_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, task_id, message, remind_at.isoformat()),
        )
        conn.commit()
        return cursor.lastrowid


def get_pending_reminders(before: datetime) -> list[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, user_id, task_id, message, remind_at
            FROM reminders
            WHERE is_sent = 0 AND remind_at <= ?
            ORDER BY remind_at ASC
            """,
            (before.isoformat(),),
        )
        return cursor.fetchall()


def mark_reminder_sent(reminder_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE reminders SET is_sent = 1 WHERE id = ?",
            (reminder_id,),
        )
        conn.commit()
