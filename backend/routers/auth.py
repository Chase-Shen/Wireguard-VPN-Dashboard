# backend/routers/auth.py

from fastapi import APIRouter

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)
