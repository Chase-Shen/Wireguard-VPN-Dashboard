from fastapi import APIRouter, Cookie, HTTPException, Response, status
from typing import Annotated

from backend.access_control import CurrentUser
from backend.database import Database
from backend.authentications import authenticate_user

from backend.schemas import (
    LoginRequest,
    MessageResponse,
    UserResponse,
)

from backend.sessions import (
    create_session,
    delete_expired_sessions,
    delete_session,
)

from backend.config import (
    SESSION_COOKIE,
    SESSION_HOURS,
)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post("/login", response_model=UserResponse)
def login(
    login_request: LoginRequest,
    response: Response,
    db: Database
):
    delete_expired_sessions(db)

    user = authenticate_user(db, login_request.username, login_request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    session_token = create_session(db, user["id"])

    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=SESSION_HOURS * 3600,
        path="/",
    )

    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
    }

@router.post("/logout", response_model=MessageResponse)
def logout(
    response: Response,
    db: Database,
    session_token: Annotated[
        str | None,
        Cookie(alias=SESSION_COOKIE),
    ] = None,
):
    if session_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No session token provided",
        )
    
    delete_session(db, session_token)

    response.delete_cookie(SESSION_COOKIE)

    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def get_current_user(
    user: CurrentUser,
):
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
    }