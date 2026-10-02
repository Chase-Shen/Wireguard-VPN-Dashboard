import sqlite3
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status

from backend.database import Database
from backend.sessions import get_user_from_session

from backend.config import SESSION_COOKIE


def require_user(
    db: Database,
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> sqlite3.Row:
    if session_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    
    user = get_user_from_session(db, session_token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token",
        )
    return user

CurrentUser = Annotated[sqlite3.Row, Depends(require_user)]

def require_admin(user: CurrentUser) -> sqlite3.Row:
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user

AdminUser = Annotated[
    sqlite3.Row,
    Depends(require_admin),
]