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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, task_number)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks (user_id)"
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_due
            ON tasks (remind_at)
            """
        )
        _migrate_tasks_table(conn)
        conn.commit()


def add_task(
    user_id: int,
    text: str,
    remind_at: datetime,
    repeat_type: str,
) -> int:
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
            (user_id, next_number, text, remind_at.isoformat(), repeat_type),
        )
        conn.commit()
        return next_number


def get_tasks(user_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT task_number, text, remind_at, repeat_type
            FROM tasks
            WHERE user_id = ?
            ORDER BY task_number ASC
            """,
            (user_id,),
        )
        return cursor.fetchall()


def get_due_tasks(before: datetime) -> list[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, user_id, task_number, text, remind_at, repeat_type
            FROM tasks
            WHERE remind_at IS NOT NULL AND remind_at <= ?
            ORDER BY remind_at ASC
            """,
            (before.isoformat(),),
        )
        return cursor.fetchall()


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
