import getpass 
import os
import sqlite3

from pwdlib import PasswordHash

DATABASE_PATH = os.environ.get(
    "WG_DASHBOARD_DB_PATH",
    "/var/lib/wg-dashboard/wg_dashboard.db",
)

password_hasher = PasswordHash.recommended()

def authenticate_user(conn: sqlite3.Connection, username: str, password: str):
    user = conn.execute(
        """
        SELECT id, username, password_hash, role, is_active
        FROM users
        WHERE username = ?
        """,
        (username,),
    ).fetchone()

    if user is None or not user["is_active"]:
        return None
    
    if not password_hasher.verify(password, user["password_hash"]):
        return None
    
    return user

def create_admin(conn: sqlite3.Connection, username: str, password: str):
    pwd_hash_value = password_hasher.hash(password)
    
    with conn:
        conn.execute(
            """
            INSERT INTO users (username, password_hash, role, is_active) 
            VALUES (?, ?, ?, ?)
            """,
            (username, pwd_hash_value, "admin", 1)
        )

def create_admin_cli():
    username = input("Enter admin username: ").strip() or "admin"
    pwd = getpass.getpass("Enter admin password: ")
    confirm_pwd = getpass.getpass("Confirm admin password: ")

    if pwd != confirm_pwd:
        raise SystemExit("Passwords do not match. Exiting.")
    
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        create_admin(conn, username, pwd)
        print(f"Admin user '{username}' created successfully.")

    except sqlite3.Error as e:
        conn.rollback()
        raise SystemExit(f"Error creating admin user: {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    create_admin_cli()


