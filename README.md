# WireGuard Dashboard

A self-hosted Vue and FastAPI dashboard for monitoring an Ubuntu WireGuard server and managing user-owned VPN devices.

> **Status:** Active development. HTTPS deployment and server monitoring work; application authentication, device provisioning, and restricted WireGuard management are still in progress.

## Stack

- Vue 3 and Vite
- FastAPI and Uvicorn
- SQLite
- WireGuard
- Caddy and systemd

## Architecture

```text
Browser --HTTPS--> Caddy
                    |-- static Vue build
                    `-- /api/* --> FastAPI on 127.0.0.1:8000
                                      |-- SQLite
                                      |-- host metrics
                                      `-- WireGuard
```

Caddy uses TCP 80/443. WireGuard uses UDP 443. FastAPI is not exposed directly to the network.

## Local Setup

Backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
uvicorn backend.api:app --host 127.0.0.1 --port 8000 --reload
```

Frontend, in another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Production frontend build:

```bash
cd frontend
npm run build
```

## Database

Production data is stored at `/var/lib/wg-dashboard/wg_dashboard.db`.

Apply pending migrations with:

```bash
sudo -u chase env \
  WG_DASHBOARD_DB_PATH=/var/lib/wg-dashboard/wg_dashboard.db \
  .venv/bin/python backend/migrate.py
```

## Documentation

- [Deployment progress](docs/deployment-progress.md)
- [WireGuard setup](docs/wireguard-setup.md)
- [Dashboard systemd service](docs/systemd-service.md)

## Security

Never commit WireGuard private keys, preshared keys, passwords, session tokens, DuckDNS tokens, databases, or production environment files. Keep the backend unprivileged and use a narrowly scoped helper for WireGuard changes.
