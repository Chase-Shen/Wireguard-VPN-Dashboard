import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash

password_hasher = PasswordHash().recommended()

SESSION_HOURS = 12 

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

def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def create_session(conn: sqlite3.Connection, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hash_session_token(token)

    expires_at = (
        datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
        ).strftime("%m-%d-%Y %H:%M:%S")

    with conn:
        conn.execute(
            """
            INSERT INTO sessions (user_id, session_token, expires_at)
            VALUES (?, ?, ?)
            """,
            (user_id, token_hash, expires_at),
        )

    return token

def get_user_from_session(conn: sqlite3.Connection, token: str):
    token_hash = hash_session_token(token)

    user = conn.execute(
        """
        SELECT users.id, users.username, users.role, users.is_active
        FROM sessions
        JOIN users ON sessions.user_id = users.id
        WHERE sessions.session_token = ? AND sessions.expires_at > CURRENT_TIMESTAMP
            AND users.is_active = 1
        """,
        (token_hash,),
    ).fetchone()

    return user

def delete_session(conn: sqlite3.Connection, token: str):
    token_hash = hash_session_token(token)

    with conn:
        conn.execute(
            """
            DELETE FROM sessions
            WHERE session_token = ?
            """,
            (token_hash,),
        )

def delete_expired_sessions(conn: sqlite3.Connection):
    with conn:
        conn.execute(
            """
            DELETE FROM sessions
            WHERE expires_at <= CURRENT_TIMESTAMP
            """
        )