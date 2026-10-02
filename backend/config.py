import os


DATABASE_PATH = os.environ.get(
    "WG_DASHBOARD_DB_PATH",
    "/var/lib/wg-dashboard/wg_dashboard.db",
)

SESSION_COOKIE = "wg_session"

SESSION_HOURS = int(
    os.environ.get(
        "WG_DASHBOARD_SESSION_HOURS",
        "12",
    )
)

LOCAL_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
]