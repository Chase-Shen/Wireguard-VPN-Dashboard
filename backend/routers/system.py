from datetime import datetime

import psutil
from fastapi import APIRouter


router = APIRouter(
    prefix="/system",
    tags=["system"],
)

@router.get("/info")
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