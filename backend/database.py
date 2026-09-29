import os
import sqlite3
from collections.abc import Generator

DATABASE_PATH = os.environ.get(
    "WG_DASHBOARD_DB_PATH",
    "/var/lib/wg-dashboard/wg_dashboard.db",
)

def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")

    return conn

def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = connect_db()
    try:
        yield conn
    finally:
        conn.close()    