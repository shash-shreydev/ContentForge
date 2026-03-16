import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.getenv("DATABASE_PATH", "contentforge.db")


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                input_content TEXT NOT NULL,
                output_type TEXT NOT NULL,
                generated_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                generation_count INTEGER NOT NULL,
                billing_cycle_start TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )


def _utc_now():
    return datetime.now(timezone.utc)


def _month_start(dt):
    return datetime(dt.year, dt.month, 1, tzinfo=timezone.utc)


def create_user(email, password_hash):
    with get_db() as conn:
        now = _utc_now().isoformat()
        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?);",
            (email, password_hash, now),
        )
        return cursor.lastrowid


def get_user_by_email(email):
    with get_db() as conn:
        return conn.execute(
            "SELECT id, email, password_hash, created_at FROM users WHERE email = ?;",
            (email,),
        ).fetchone()


def get_user_by_id(user_id):
    with get_db() as conn:
        return conn.execute(
            "SELECT id, email, password_hash, created_at FROM users WHERE id = ?;",
            (user_id,),
        ).fetchone()


def create_generations(user_id, input_content, outputs):
    with get_db() as conn:
        now = _utc_now().isoformat()
        for output_type, generated_text in outputs.items():
            conn.execute(
                """
                INSERT INTO generations
                    (user_id, input_content, output_type, generated_text, created_at)
                VALUES (?, ?, ?, ?, ?);
                """,
                (user_id, input_content, output_type, generated_text, now),
            )


def _get_or_reset_usage(conn, user_id):
    row = conn.execute(
        "SELECT generation_count, billing_cycle_start FROM usage WHERE user_id = ?;",
        (user_id,),
    ).fetchone()
    now = _utc_now()
    month_start = _month_start(now)
    if row is None:
        conn.execute(
            "INSERT INTO usage (user_id, generation_count, billing_cycle_start) VALUES (?, ?, ?);",
            (user_id, 0, month_start.isoformat()),
        )
        return 0, month_start
    stored_start = datetime.fromisoformat(row["billing_cycle_start"])
    if stored_start.year != month_start.year or stored_start.month != month_start.month:
        conn.execute(
            "UPDATE usage SET generation_count = 0, billing_cycle_start = ? WHERE user_id = ?;",
            (month_start.isoformat(), user_id),
        )
        return 0, month_start
    return row["generation_count"], stored_start


def get_remaining_generations(user_id, limit=3):
    with get_db() as conn:
        count, _ = _get_or_reset_usage(conn, user_id)
        return max(0, limit - count)


def increment_generation_count(user_id):
    with get_db() as conn:
        count, _ = _get_or_reset_usage(conn, user_id)
        new_count = count + 1
        conn.execute(
            "UPDATE usage SET generation_count = ? WHERE user_id = ?;",
            (new_count, user_id),
        )
        return new_count
