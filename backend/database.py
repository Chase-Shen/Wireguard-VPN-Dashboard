import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

DATABASE_PATH = "wg_dashboard.db"

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    """Initialize database with tables"""
    with get_db() as conn:
        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
        """)

        # Devices table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                public_key TEXT UNIQUE NOT NULL,
                device_name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
        """)


# ========== User Functions ==========

def add_user(username: str, email: str, password_hash: str = None) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        return cursor.lastrowid

def get_user(user_id: int):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", 
            (user_id,)
            ).fetchone()
        return dict(row) if row else None

def get_user_by_username(username: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
            ).fetchone()
        return dict(row) if row else None

def get_all_users():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY username").fetchall()
        return [dict(row) for row in rows]

def update_user(user_id: int, username: str = None, email: str = None, password_hash: str = None):
    with get_db() as conn:
        if username:
            conn.execute("UPDATE users SET username = ? WHERE id = ?", (username, user_id))
        if email:
            conn.execute("UPDATE users SET email = ? WHERE id = ?", (email, user_id))
        if password_hash:
            conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))

def delete_user(user_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

# ========== Device Functions ==========
def add_device(public_key: str, device_name: str, user_id: int) -> int:
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO devices (public_key, device_name, user_id) VALUES (?, ?, ?)",
            (public_key, device_name, user_id)
        )
        return cursor.lastrowid

def get_device(device_id: int):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM devices WHERE id = ?",
            (device_id,)
        ).fetchone()
        return dict(row) if row else None