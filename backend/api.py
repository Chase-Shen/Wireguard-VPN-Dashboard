from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import psutil
from datetime import datetime

app = FastAPI(title="WireGuard Dashboard")

# Add CORS middleware to allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                   "http://localhost:5174"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/system/info")
def system_info():
    return {
        "uptime": datetime.now().timestamp() - psutil.boot_time(),
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "used": psutil.virtual_memory().used,
            "percent": psutil.virtual_memory().percent,
        },
        "disk": {
            "total": psutil.disk_usage('/').total,
            "free": psutil.disk_usage('/').free,
            "used": psutil.disk_usage('/').used,
            "percent": psutil.disk_usage('/').percent,
        },
        "timestamp": datetime.now().isoformat()        
    }
    
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
