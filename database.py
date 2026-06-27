import sqlite3

from config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate_tasks_table(conn: sqlite3.Connection) -> None:
    columns = {
        row["name"] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
    }

    if "task_number" in columns:
        return

    conn.execute("ALTER TABLE tasks ADD COLUMN task_number INTEGER")

    user_ids = conn.execute(
        "SELECT DISTINCT user_id FROM tasks ORDER BY user_id"
    ).fetchall()

    for row in user_ids:
        user_id = row["user_id"]
        tasks = conn.execute(
            """
            SELECT id
            FROM tasks
            WHERE user_id = ?
            ORDER BY id ASC
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


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task_number INTEGER NOT NULL,
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, task_number)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks (user_id)"
        )
        _migrate_tasks_table(conn)
        conn.commit()


def add_task(user_id: int, text: str) -> tuple[int, int]:
    with get_connection() as conn:
        next_number = conn.execute(
            """
            SELECT COALESCE(MAX(task_number), 0) + 1 AS next_number
            FROM tasks
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()["next_number"]

        cursor = conn.execute(
            """
            INSERT INTO tasks (user_id, task_number, text)
            VALUES (?, ?, ?)
            """,
            (user_id, next_number, text),
        )
        conn.commit()
        return next_number, cursor.lastrowid


def get_tasks(user_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT
                t.task_number,
                t.text,
                r.remind_at
            FROM tasks t
            LEFT JOIN reminders r
                ON r.task_id = t.id AND r.is_sent = 0
            WHERE t.user_id = ?
            ORDER BY t.task_number ASC
            """,
            (user_id,),
        )
        return cursor.fetchall()


def count_tasks(user_id: int) -> int:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS total FROM tasks WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return row["total"]


def delete_task(user_id: int, task_number: int) -> bool:
    with get_connection() as conn:
        task_id = conn.execute(
            """
            SELECT id
            FROM tasks
            WHERE user_id = ? AND task_number = ?
            """,
            (user_id, task_number),
        ).fetchone()

        if task_id is None:
            return False

        conn.execute(
            "DELETE FROM reminders WHERE task_id = ?",
            (task_id["id"],),
        )
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


def clear_all_tasks(user_id: int) -> int:
    with get_connection() as conn:
        conn.execute("DELETE FROM reminders WHERE user_id = ?", (user_id,))
        cursor = conn.execute(
            "DELETE FROM tasks WHERE user_id = ?",
            (user_id,),
        )
        conn.commit()
        return cursor.rowcount


def get_task_id(user_id: int, task_number: int) -> int | None:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id
            FROM tasks
            WHERE user_id = ? AND task_number = ?
            """,
            (user_id, task_number),
        ).fetchone()
        return row["id"] if row else None


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
