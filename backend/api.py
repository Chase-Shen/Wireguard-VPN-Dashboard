from fastapi.middleware.cors import CORSMiddleware
import subprocess
from fastapi import FastAPI

from backend.routers import system, auth
from backend.config import LOCAL_ORIGINS

app = FastAPI(title="WireGuard Dashboard")

app.include_router(system.router)
app.include_router(auth.router)


# Add CORS middleware to allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_ORIGINS,
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
