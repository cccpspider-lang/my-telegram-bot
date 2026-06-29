import sqlite3
from datetime import datetime

from config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate_tasks_table(conn: sqlite3.Connection) -> None:
    columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
    }

    if "remind_at" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN remind_at TIMESTAMP")

    if "repeat_type" not in columns:
        conn.execute(
            "ALTER TABLE tasks ADD COLUMN repeat_type TEXT NOT NULL DEFAULT 'once'"
        )

    if "is_completed" not in columns:
        conn.execute(
            "ALTER TABLE tasks ADD COLUMN is_completed INTEGER NOT NULL DEFAULT 0"
        )

    if "completed_at" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN completed_at TIMESTAMP")

    if "task_number" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN task_number INTEGER")
        user_ids = conn.execute(
            "SELECT DISTINCT user_id FROM tasks ORDER BY user_id"
        ).fetchall()
        for row in user_ids:
            user_id = row["user_id"]
            tasks = conn.execute(
                """
                SELECT id FROM tasks WHERE user_id = ? ORDER BY id ASC
                """,
                (user_id,),
            ).fetchall()
            for index, task in enumerate(tasks, start=1):
                conn.execute(
                    "UPDATE tasks SET task_number = ? WHERE id = ?",
                    (index, task["id"]),
                )

    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_user_task_number
        ON tasks (user_id, task_number)
        """
    )
    _migrate_reminders_into_tasks(conn)


def _migrate_reminders_into_tasks(conn: sqlite3.Connection) -> None:
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "reminders" not in tables:
        return

    rows = conn.execute(
        """
        SELECT task_id, remind_at, repeat_type
        FROM reminders
        WHERE task_id IS NOT NULL
        """
    ).fetchall()

    for row in rows:
        conn.execute(
            """
            UPDATE tasks
            SET remind_at = ?, repeat_type = ?
            WHERE id = ? AND remind_at IS NULL
            """,
            (row["remind_at"], row["repeat_type"], row["task_id"]),
        )

    conn.execute("DROP TABLE IF EXISTS reminders")


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_number INTEGER NOT NULL,
                text TEXT NOT NULL,
                remind_at TIMESTAMP,
                repeat_type TEXT NOT NULL DEFAULT 'once',
                is_completed INTEGER NOT NULL DEFAULT 0,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, task_number)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks (user_id)"
        )
        _migrate_tasks_table(conn)
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_due
            ON tasks (remind_at)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS morning_digest_sent (
                user_id INTEGER NOT NULL,
                sent_date TEXT NOT NULL,
                PRIMARY KEY (user_id, sent_date)
            )
            """
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO users (user_id, first_name)
            SELECT DISTINCT user_id, 'друг' FROM tasks
            """
        )
        conn.commit()


def upsert_user(user_id: int, first_name: str | None) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, first_name, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name = excluded.first_name,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, first_name or "друг"),
        )
        conn.commit()


def get_all_users() -> list[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT user_id, first_name
            FROM users
            ORDER BY user_id ASC
            """
        )
        return cursor.fetchall()


def was_morning_digest_sent(user_id: int, sent_date: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM morning_digest_sent
            WHERE user_id = ? AND sent_date = ?
            """,
            (user_id, sent_date),
        ).fetchone()
        return row is not None


def mark_morning_digest_sent(user_id: int, sent_date: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO morning_digest_sent (user_id, sent_date)
            VALUES (?, ?)
            """,
            (user_id, sent_date),
        )
        conn.commit()


def add_task(
    user_id: int,
    text: str,
    remind_at: datetime | None,
    repeat_type: str,
) -> int:
    remind_at_value = remind_at.isoformat() if remind_at else None
    with get_connection() as conn:
        next_number = conn.execute(
            """
            SELECT COALESCE(MAX(task_number), 0) + 1 AS next_number
            FROM tasks
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()["next_number"]

        conn.execute(
            """
            INSERT INTO tasks (user_id, task_number, text, remind_at, repeat_type)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, next_number, text, remind_at_value, repeat_type),
        )
        conn.commit()
        return next_number


def get_tasks(user_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT task_number, text, remind_at, repeat_type
            FROM tasks
            WHERE user_id = ? AND is_completed = 0
            ORDER BY task_number ASC
            """,
            (user_id,),
        )
        return cursor.fetchall()


def get_today_tasks(user_id: int, today_str: str) -> list[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT task_number, text
            FROM tasks
            WHERE user_id = ? AND is_completed = 0
            AND (remind_at IS NULL OR substr(remind_at, 1, 10) = ?)
            ORDER BY task_number ASC
            """,
            (user_id, today_str),
        )
        return cursor.fetchall()


def get_due_tasks(before: datetime) -> list[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, user_id, task_number, text, remind_at, repeat_type
            FROM tasks
            WHERE remind_at IS NOT NULL
            AND remind_at <= ?
            AND is_completed = 0
            ORDER BY remind_at ASC
            """,
            (before.isoformat(),),
        )
        return cursor.fetchall()


def complete_task(user_id: int, task_number: int, completed_at: datetime) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE tasks
            SET is_completed = 1, completed_at = ?
            WHERE user_id = ? AND task_number = ? AND is_completed = 0
            """,
            (completed_at.isoformat(), user_id, task_number),
        )
        if cursor.rowcount == 0:
            return False
        conn.commit()
        return True


def count_completed_on_date(user_id: int, date_str: str) -> int:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS count
            FROM tasks
            WHERE user_id = ? AND is_completed = 1
            AND substr(completed_at, 1, 10) = ?
            """,
            (user_id, date_str),
        ).fetchone()
        return row["count"]


def get_completion_dates(user_id: int) -> list[str]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT DISTINCT substr(completed_at, 1, 10) AS completion_date
            FROM tasks
            WHERE user_id = ? AND is_completed = 1 AND completed_at IS NOT NULL
            ORDER BY completion_date DESC
            """,
            (user_id,),
        )
        return [row["completion_date"] for row in cursor.fetchall()]


def reschedule_task(task_id: int, remind_at: datetime) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET remind_at = ? WHERE id = ?",
            (remind_at.isoformat(), task_id),
        )
        conn.commit()


def clear_task_reminder(task_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE tasks SET remind_at = NULL WHERE id = ?",
            (task_id,),
        )
        conn.commit()


def delete_task(user_id: int, task_number: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            DELETE FROM tasks
            WHERE user_id = ? AND task_number = ?
            """,
            (user_id, task_number),
        )

        if cursor.rowcount == 0:
            return False

        _renumber_tasks(conn, user_id)
        conn.commit()
        return True


def _renumber_tasks(conn: sqlite3.Connection, user_id: int) -> None:
    remaining = conn.execute(
        """
        SELECT id
        FROM tasks
        WHERE user_id = ?
        ORDER BY task_number ASC
        """,
        (user_id,),
    ).fetchall()

    for index, task in enumerate(remaining, start=1):
        conn.execute(
            "UPDATE tasks SET task_number = ? WHERE id = ? AND user_id = ?",
            (index, task["id"], user_id),
        )
