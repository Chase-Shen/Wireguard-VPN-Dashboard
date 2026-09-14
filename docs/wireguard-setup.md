# WireGuard Server Setup

This guide reproduces the VPN used by the dashboard on a fresh Ubuntu server. Use a local console or LAN SSH session so a mistake cannot lock you out.

## Target Configuration

```text
Interface:       wg0
Server LAN IP:   192.168.1.254
VPN subnet:      10.20.0.0/24
Server VPN IP:   10.20.0.1/24
Public endpoint: almightydoge.duckdns.org:443
Transport:       UDP
```

## 1. Install WireGuard

```bash
sudo apt update
sudo apt install -y wireguard
wg --version
```

## 2. Enable IPv4 Forwarding

Create `/etc/sysctl.d/99-wireguard-forwarding.conf`:

```text
net.ipv4.ip_forward=1
```

Apply and verify it:

```bash
sudo sysctl --system
sysctl net.ipv4.ip_forward
```

The value must be `1`.

## 3. Generate Server Keys

```bash
sudo install -d -m 700 /etc/wireguard
sudo sh -c 'umask 077; wg genkey > /etc/wireguard/server-private.key'
sudo sh -c 'wg pubkey < /etc/wireguard/server-private.key > /etc/wireguard/server-public.key'
sudo chmod 600 /etc/wireguard/server-private.key
sudo chmod 644 /etc/wireguard/server-public.key
```

The public key may be shared with clients. Never paste or commit the private key.

## 4. Identify The Outbound Interface

```bash
ip route show default
```

This server uses `enp0s31f6`. Substitute the reported interface on different hardware.

## 5. Create `/etc/wireguard/wg0.conf`

```ini
[Interface]
Address = 10.20.0.1/24
ListenPort = 443
PrivateKey = SERVER_PRIVATE_KEY
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -A FORWARD -o wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o enp0s31f6 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -D FORWARD -o wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o enp0s31f6 -j MASQUERADE
```

Insert the private key locally, then protect the file:

```bash
sudo chmod 600 /etc/wireguard/wg0.conf
```

Do not enable `SaveConfig` when the dashboard will manage a canonical configuration file; it can overwrite deliberate file edits when the interface stops.

## 6. Start The VPN Service

```bash
sudo systemctl enable --now wg-quick@wg0
sudo systemctl status wg-quick@wg0 --no-pager
sudo wg show wg0
ip -brief address show wg0
```

The interface should have `10.20.0.1/24` and listen on UDP 443.

## 7. Configure DNS And Double NAT

Configure DuckDNS so `almightydoge.duckdns.org` tracks the public IPv4 address. Keep its token outside Git and restrict the updater script:

```bash
chmod 700 /home/chase/duckdns/duck.sh
```

Forward UDP 443 through both routers:

```text
Main router UDP 443 -> sub-router WAN address:443
Sub-router UDP 443  -> 192.168.1.254:443
```

Reserve the sub-router WAN address and Ubuntu's `192.168.1.254` address so DHCP cannot change either destination.

## 8. Add A Client

Generate keys on the client so its private key never leaves that device:

```bash
umask 077
wg genkey > client-private.key
wg pubkey < client-private.key > client-public.key
```

Add the public half to the server's `wg0.conf`:

```ini
[Peer]
PublicKey = CLIENT_PUBLIC_KEY
AllowedIPs = 10.20.0.2/32
```

Apply it live without stopping the interface:

```bash
sudo wg set wg0 peer CLIENT_PUBLIC_KEY allowed-ips 10.20.0.2/32
```

Create the client configuration:

```ini
[Interface]
PrivateKey = CLIENT_PRIVATE_KEY
Address = 10.20.0.2/32
DNS = 1.1.1.1

[Peer]
PublicKey = SERVER_PUBLIC_KEY
Endpoint = almightydoge.duckdns.org:443
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
```

Assign a unique `/32` address and key pair to every peer. The current server already has a peer at `10.20.0.254/32`, which must remain reserved.

## 9. Verify The Tunnel

```bash
sudo wg show wg0
```

After connecting a client, confirm a recent handshake and increasing transfer counters. Test access to `10.20.0.1` and, for a full tunnel, public internet access.

## 10. Share Port 443 With Caddy

HTTPS uses TCP 443 and can coexist with WireGuard on UDP 443. Caddy's optional HTTP/3 also uses UDP 443, so disable HTTP/3 in `/etc/caddy/Caddyfile`:

```caddyfile
{
    servers {
        protocols h1 h2
    }
}
```

Verify WireGuard owns UDP 443 and Caddy owns TCP 443:

```bash
sudo ss -lntup | grep ':443'
```

## Safety Notes

- Back up `/etc/wireguard/wg0.conf` before changing peers.
- Never expose private or preshared keys through logs or peer APIs.
- Apply live changes with `wg set` and update persistent configuration in the same operation.
- Keep LAN access during port, firewall, or routing changes.
- Give the dashboard a narrowly scoped helper, never unrestricted passwordless `sudo`.
