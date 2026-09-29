import getpass 
import os
import sqlite3

from pwdlib import PasswordHash

DATABASE_PATH = os.environ.get(
    "WG_DASHBOARD_DB_PATH",
    "/var/lib/wg-dashboard/wg_dashboard.db",
)

pwd_hash = PasswordHash.recommended()

def create_admin():
    username = input("Enter admin username: ").strip() or "admin"
    pwd = getpass.getpass("Enter admin password: ")
    confirm_pwd = getpass.getpass("Confirm admin password: ")

    if pwd != confirm_pwd:
        raise SystemExit("Passwords do not match. Exiting.")

    pwd_hash_value = pwd_hash.hash(pwd)
    
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute(
            """
            INSERT INTO users (username, password_hash, role, is_active) 
            VALUES (?, ?, ?, ?)
            """,
            (username, pwd_hash_value, "admin", 1)
        )
        conn.commit()
        print(f"Admin user '{username}' created successfully.")

    except sqlite3.Error as e:
        conn.rollback()
        raise SystemExit(f"Error creating admin user: {e}")

    finally:
        conn.close()

if __name__ == "__main__":
    create_admin()


