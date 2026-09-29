import os 
import sqlite3
from pathlib import Path

DATABASE_PATH = Path(
    os.environ.get(
        "WG_DASHBOARD_DB_PATH", 
        "/var/lib/wg-dashboard/wg_dashboard.db",
    )
)

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

def connect_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    return conn

def create_migrations_table(conn):
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def is_migrations_applied(conn, filename):
    with conn:
        row = conn.execute(
            """
            SELECT filename FROM migrations 
            WHERE filename = ?
            """,
            (filename,)).fetchone()

    return row is not None


def apply_migration(conn, migration_file):
    with open(migration_file, 'r', encoding='utf-8') as file:
        sql_script = file.read()
    with conn:
        conn.executescript(sql_script)
        conn.execute(
            "INSERT INTO migrations (filename) VALUES (?)",
            (migration_file.name,)
        )
    print(f"Applied migration: {migration_file.name}")

def migrate():
    with connect_db() as conn:
        create_migrations_table(conn)

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    for migration_file in migration_files:
        if not is_migrations_applied(conn, migration_file.name):
            apply_migration(conn, migration_file)
        else:
            print(f"Skipping already applied migration: {migration_file.name}")

    conn.close()

if __name__ == "__main__":
    migrate()
