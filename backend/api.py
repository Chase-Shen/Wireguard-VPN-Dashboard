from fastapi.middleware.cors import CORSMiddleware
import subprocess
import sqlite3
from pydantic import BaseModel, Field

from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    HTTPException,
    Response,
    status,
)

from backend.auth import (
    authenticate_user,
    create_session,
    delete_expired_sessions,
    delete_session,
    get_user_from_session,
)

from backend.database import get_db
from backend.routers import system

app = FastAPI(title="WireGuard Dashboard")

app.include_router(system.router)

Database = Annotated[
    sqlite3.Connection,
    Depends(get_db),
]

SESSION_COOKIE = "wg_session"
SESSION_SECONDS = 12 * 60 * 60

class LoginRequest(BaseModel):
    username: str = Field(..., example="admin")
    password: str = Field(..., example="password")

# Add CORS middleware to allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                   "http://localhost:5174"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    
@app.get("/wg/peers")
async def wg_peers():
    try:
        out = subprocess.check_output(["sudo", "wg", "show", "all", "dump"])
        lines = out.decode().splitlines()

        peers = []
        for line in lines[1:]:  # Skip the first line (interface info)
            parts = line.split('\t')
            if len(parts) >= 9:  # Ensure having all peer fields
                peer_info = {
                    "interface": parts[0],
                    "public_key": parts[1],
                    "preshared_key": parts[2] if parts[2] != "(none)" else None,
                    "endpoint": parts[3] if parts[3] != "(none)" else None,
                    "ip": parts[4],
                    "latest_handshake": int(parts[5]) if parts[5] != "0" else 0,
                    "rx_bytes": int(parts[6]),
                    "tx_bytes": int(parts[7]),
                    "persistent_keepalive": int(parts[8]) if parts[8] != "off" else 0,
                }
                peers.append(peer_info)
        return {"status": "success", "data": peers}

    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": str(e)}
