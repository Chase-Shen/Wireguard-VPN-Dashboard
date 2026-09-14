# Dashboard Systemd Service

This guide makes FastAPI start after boot, restart after failure, and remain accessible only through Caddy.

## Create The Unit

Create `/etc/systemd/system/wg-dashboard.service`:

```ini
[Unit]
Description=WireGuard Dashboard API
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=chase
Group=chase
WorkingDirectory=/home/chase/wg-dashboard
ExecStart=/home/chase/wg-dashboard/.venv/bin/uvicorn backend.api:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/chase/wg-dashboard/backend

[Install]
WantedBy=multi-user.target
```

The service runs without root, listens only on loopback, cannot acquire new privileges, and has a restricted writable path.

## Enable And Verify

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now wg-dashboard
sudo systemctl status wg-dashboard --no-pager
curl http://127.0.0.1:8000/system/info
curl -u admin https://almightydoge.duckdns.org/api/system/info
sudo ss -lntp | grep ':8000'
```

The listener must be `127.0.0.1:8000`, not every network interface.

## Logs And Restarts

```bash
sudo journalctl -u wg-dashboard -n 50 --no-pager
sudo journalctl -u wg-dashboard -f
sudo systemctl restart wg-dashboard
```

Run `sudo systemctl daemon-reload` before restarting after a unit-file change.

## Database Update

When persistence is added, create `/var/lib/wg-dashboard` and replace the writable path with:

```ini
Environment=WG_DASHBOARD_DB_PATH=/var/lib/wg-dashboard/wg_dashboard.db
ReadWritePaths=/var/lib/wg-dashboard
```

The current `sudo wg` call cannot work inside this hardened service. Implement a narrow privileged helper instead of weakening the service.
