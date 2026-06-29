import sqlite3
from datetime import datetime

from database import get_connection
from reminders.constants import REPEAT_ONCE


def init_reminders_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_id INTEGER,
            reminder_number INTEGER,
            message TEXT NOT NULL,
            remind_at TIMESTAMP NOT NULL,
            repeat_type TEXT NOT NULL DEFAULT 'once',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE SET NULL
        )
        """
    )
    _migrate_reminders_table(conn)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders (user_id)"
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reminders_due
        ON reminders (remind_at)
        """
    )


def _migrate_reminders_table(conn: sqlite3.Connection) -> None:
    columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(reminders)").fetchall()
    }

    if "is_sent" in columns:
        conn.execute(
            """
            CREATE TABLE reminders_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_id INTEGER,
                reminder_number INTEGER,
                message TEXT NOT NULL,
                remind_at TIMESTAMP NOT NULL,
                repeat_type TEXT NOT NULL DEFAULT 'once',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE SET NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO reminders_new (
                id, user_id, task_id, message, remind_at, repeat_type, created_at
            )
            SELECT
                id,
                user_id,
                task_id,
                message,
                remind_at,
                'once',
                created_at
            FROM reminders
            WHERE is_sent = 0
            """
        )
        conn.execute("DROP TABLE reminders")
        conn.execute("ALTER TABLE reminders_new RENAME TO reminders")
        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(reminders)").fetchall()
        }

    if "repeat_type" not in columns:
        conn.execute(
            "ALTER TABLE reminders ADD COLUMN repeat_type TEXT NOT NULL DEFAULT 'once'"
        )

    if "reminder_number" not in columns:
        conn.execute("ALTER TABLE reminders ADD COLUMN reminder_number INTEGER")

    _assign_reminder_numbers(conn)


def _assign_reminder_numbers(conn: sqlite3.Connection) -> None:
    user_ids = conn.execute(
        """
        SELECT DISTINCT user_id
        FROM reminders
        WHERE task_id IS NULL
        ORDER BY user_id
        """
    ).fetchall()

    for row in user_ids:
        user_id = row["user_id"]
        reminders = conn.execute(
            """
            SELECT id
            FROM reminders
            WHERE user_id = ? AND task_id IS NULL
            ORDER BY id ASC
            """,
            (user_id,),
        ).fetchall()

        for index, reminder in enumerate(reminders, start=1):
            conn.execute(
                """
                UPDATE reminders
                SET reminder_number = ?
                WHERE id = ? AND user_id = ?
                """,
                (index, reminder["id"], user_id),
            )


def _next_reminder_number(conn: sqlite3.Connection, user_id: int) -> int:
    row = conn.execute(
        """
        SELECT COALESCE(MAX(reminder_number), 0) + 1 AS next_number
        FROM reminders
        WHERE user_id = ? AND task_id IS NULL
        """,
        (user_id,),
    ).fetchone()
    return row["next_number"]


def create_reminder(
    user_id: int,
    message: str,
    remind_at: datetime,
    task_id: int | None = None,
    repeat_type: str = REPEAT_ONCE,
) -> tuple[int, int | None]:
    with get_connection() as conn:
        reminder_number = None
        if task_id is None:
            reminder_number = _next_reminder_number(conn, user_id)

        cursor = conn.execute(
            """
            INSERT INTO reminders (
                user_id, task_id, reminder_number, message, remind_at, repeat_type
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                task_id,
                reminder_number,
                message,
                remind_at.isoformat(),
                repeat_type,
            ),
        )
        conn.commit()
        return cursor.lastrowid, reminder_number


def get_pending_reminders(before: datetime) -> list[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, user_id, task_id, message, remind_at, repeat_type
            FROM reminders
            WHERE remind_at <= ?
            ORDER BY remind_at ASC
            """,
            (before.isoformat(),),
        )
        return cursor.fetchall()


def delete_reminder_by_id(reminder_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        conn.commit()


def reschedule_reminder(reminder_id: int, remind_at: datetime) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE reminders SET remind_at = ? WHERE id = ?",
            (remind_at.isoformat(), reminder_id),
        )
        conn.commit()


def get_user_reminders(user_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT reminder_number, message, remind_at, repeat_type
            FROM reminders
            WHERE user_id = ? AND task_id IS NULL
            ORDER BY reminder_number ASC
            """,
            (user_id,),
        )
        return cursor.fetchall()


def delete_user_reminder(user_id: int, reminder_number: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            DELETE FROM reminders
            WHERE user_id = ? AND task_id IS NULL AND reminder_number = ?
            """,
            (user_id, reminder_number),
        )

        if cursor.rowcount == 0:
            return False

        _renumber_user_reminders(conn, user_id)
        conn.commit()
        return True


def _renumber_user_reminders(conn: sqlite3.Connection, user_id: int) -> None:
    reminders = conn.execute(
        """
        SELECT id
        FROM reminders
        WHERE user_id = ? AND task_id IS NULL
        ORDER BY reminder_number ASC
        """,
        (user_id,),
    ).fetchall()

    for index, reminder in enumerate(reminders, start=1):
        conn.execute(
            """
            UPDATE reminders
            SET reminder_number = ?
            WHERE id = ? AND user_id = ?
            """,
            (index, reminder["id"], user_id),
        )
