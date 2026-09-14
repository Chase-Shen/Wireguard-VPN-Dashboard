# WireGuard Dashboard Deployment Progress

Last updated: 2026-09-11

## Purpose

This document records the deployment work completed for the WireGuard dashboard, explains why each part is configured this way, and identifies the next safe implementation step. It intentionally excludes passwords, password hashes, DuckDNS tokens, WireGuard private keys, and preshared keys.

## Deployment Architecture

The dashboard runs on the same Ubuntu server as WireGuard because its backend needs to read host metrics and manage the local `wg0` interface.

```text
Internet
   |
   v
Main router
   |
   v
Sub-router (NAT)
   |
   v
Ubuntu server: 192.168.1.254
   |-- Caddy: TCP 80 and TCP 443
   |-- WireGuard: UDP 443
   `-- FastAPI: 127.0.0.1:8000 (not publicly forwarded)
```

The public hostname is `almightydoge.duckdns.org`. DuckDNS currently points it to the network's public IPv4 address.

## WireGuard Configuration Confirmed

- Interface: `wg0`
- Server tunnel address: `10.20.0.1/24`
- Client address range: `10.20.0.2` through `10.20.0.254`
- Listen port: UDP `443`
- One existing peer uses `10.20.0.254/32`

The server address and existing peer address must be reserved when automatic device address allocation is implemented.

WireGuard remains on UDP 443 because restrictive networks are more likely to permit it than the conventional UDP 51820 port. WireGuard traffic and HTTPS can share port number 443 because they use different transport protocols.

## Router Forwarding

The network uses double NAT. Port forwarding is configured in two stages.

The main router forwards these ports to the sub-router's WAN address:

| Transport | External port | Purpose |
| --- | ---: | --- |
| TCP | 80 | HTTP redirect and certificate validation |
| TCP | 443 | HTTPS dashboard |
| UDP | 443 | WireGuard |

The sub-router forwards the same ports to the Ubuntu server at `192.168.1.254`:

| Transport | External port | Internal destination |
| --- | ---: | --- |
| TCP | 80 | `192.168.1.254:80` |
| TCP | 443 | `192.168.1.254:443` |
| UDP | 443 | `192.168.1.254:443` |

Port `8000` must not be forwarded. FastAPI will listen only on the loopback address and will be reached through Caddy.

## Application Preparation

A Python virtual environment was created at `~/wg-dashboard/.venv`. The backend dependencies were installed and recorded in `backend/requirements.txt`.

The frontend API base URL in `frontend/src/App.vue` was changed from a development-only localhost URL to:

```js
const API_URL = '/api'
```

This is important because `localhost` in browser code refers to the visitor's computer. The relative `/api` URL sends requests to the public dashboard origin, where Caddy can forward them privately to FastAPI.

Unused Axios dependencies were removed. Both production and complete `npm audit` checks then reported zero known vulnerabilities.

The Vue production build completed successfully and produced static files under `frontend/dist/`. Those files were copied to `/srv/wg-dashboard` for Caddy to serve.

## Caddy And HTTPS

Caddy 2.6.2 was installed and configured for `almightydoge.duckdns.org`. Temporary HTTP Basic Authentication protects the entire preview with the username `admin`. The password and its hash are deliberately omitted from this document.

Caddy initially failed to load the HTTPS configuration because it enabled HTTP/3. HTTP/3 uses UDP 443, which was already occupied by WireGuard. The Caddy global configuration was changed to enable only HTTP/1.1 and HTTP/2:

```caddyfile
{
    servers {
        protocols h1 h2
    }
}
```

This leaves the final port ownership as:

```text
UDP 443 -> WireGuard
TCP 443 -> Caddy HTTPS
TCP 80  -> Caddy HTTP redirect/certificate handling
```

Socket inspection confirmed that WireGuard is listening on UDP 443 and Caddy is listening on TCP 443. Logging into `https://almightydoge.duckdns.org` from outside succeeded, confirming DNS, both router forwarding layers, TLS, Caddy, and temporary authentication.

## Security Notes

- The DuckDNS token appeared in a screenshot and must be rotated.
- The updated token must not be committed to Git or included in documentation.
- The DuckDNS updater script should be readable only by its owner, for example mode `700`.
- Basic Authentication is temporary protection for the preview, not the finished application login system.
- The current backend must not run as root.
- The current direct `sudo wg` call must be replaced with a narrowly scoped privileged helper before peer management is enabled publicly.
- WireGuard private keys and preshared keys must never be returned by peer-list endpoints or written to application logs.

## Current Pause Point

HTTPS deployment and login are working. FastAPI has been tested manually on `127.0.0.1:8000`; its `/system/info` endpoint returned valid server metrics.

The persistent FastAPI system service has not been created yet. This was intentionally paused so the deployment work could be documented first.

## Next Steps

1. Create a hardened `wg-dashboard.service` systemd unit that runs FastAPI as the unprivileged `chase` user on `127.0.0.1:8000`.
2. Verify `/api/system/info` through Caddy while authenticated.
3. Design and apply versioned SQLite migrations for administrators, sessions, devices, and audit events.
4. Replace temporary Basic Authentication with application authentication and MFA.
5. Implement a restricted WireGuard management helper.
6. Import the existing peer and implement transactional device creation and revocation.
7. Complete and test the Vue dashboard workflows.
8. Add backup, recovery, upgrade, and rollback procedures.

## Useful Verification Commands

Check the network listeners:

```bash
sudo ss -lntup | grep -E ':(80|443|8000)'
```

Check Caddy:

```bash
sudo systemctl status caddy --no-pager
sudo journalctl -u caddy -n 50 --no-pager
```

Validate the Caddy configuration:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
```

Build the frontend after a source change:

```bash
cd ~/wg-dashboard/frontend
npm ci
npm run build
sudo cp -a dist/. /srv/wg-dashboard/
```

The copy command above updates the deployed preview, but a later deployment script should replace it with an atomic release process so partially copied builds cannot be served.
