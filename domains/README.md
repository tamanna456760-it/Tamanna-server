# Tamanna AI Domain Deployment

Owner: HM INSAN ALI

## Public hostnames

- https://www.tamanna.com — primary website.
- https://tamanna.com — redirects to the primary website.
- https://tamanna.io and https://www.tamanna.io — redirect to the primary website.
- https://api.tamanna.com — reverse proxy to the orchestrator on 127.0.0.1:8000.
- admin.tamanna.com — planned only; do not publish DNS or expose it until an authenticated admin application exists.
- Tor v3 — optional; Tor generates its own 56-character address ending in .onion. The requested label Tamanna.onion cannot be selected as an exact v3 address.

## Required DNS records

Create these at the authoritative DNS provider after confirming the server public IPv4 address:

| Type | Name | Value |
|---|---|---|
| A | @ | YOUR_SERVER_PUBLIC_IPV4 |
| A | www | YOUR_SERVER_PUBLIC_IPV4 |
| A | api | YOUR_SERVER_PUBLIC_IPV4 |
| A | @ (tamanna.io zone) | YOUR_SERVER_PUBLIC_IPV4 |
| A | www (tamanna.io zone) | YOUR_SERVER_PUBLIC_IPV4 |

Replace the placeholder with the real public IP. If using a DNS proxy/CDN, temporarily use DNS-only mode while issuing the HTTP-01 certificate. Do not create AAAA records unless the server has working public IPv6.

## Server prerequisites

- Ubuntu server with a stable public IP and inbound TCP ports 80 and 443 reachable.
- Nginx installed on the host.
- Docker Engine and Docker Compose plugin installed.
- DNS for all five certificate names pointing to this server.
- A real frontend index.html in /var/www/tamanna.

## First-time deployment

1. Copy .env.example to .env on the server only.
2. Generate a strong token: python3 -c 'import secrets; print(secrets.token_urlsafe(48))'.
3. Put it in the server .env as ORCHESTRATOR_TOKEN=... . Never commit .env.
4. Create persistent data directory: sudo mkdir -p data.
5. Start the API: docker compose up -d --build.
6. Confirm locally: curl -fsS http://127.0.0.1:8000/health.
7. Install deploy/nginx/tamanna-http-bootstrap.conf into Nginx sites-enabled, run sudo nginx -t, then reload Nginx.
8. Issue one SAN certificate:
   sudo certbot certonly --webroot -w /var/www/html -d tamanna.com -d www.tamanna.com -d tamanna.io -d www.tamanna.io -d api.tamanna.com
9. Install deploy/nginx/tamanna-domains.conf into Nginx sites-enabled, run sudo nginx -t, and reload Nginx.
10. Verify each hostname and certificate before announcing the service live.

## Security notes

- .env, TLS private keys, Tor private keys, database files, logs and backups must remain on the server and outside Git.
- .gitignore prevents new accidental additions but does not untrack a file already committed or erase Git history. If a real secret was committed, rotate it first and plan history cleanup separately.
- The API report endpoint requires a configured ORCHESTRATOR_TOKEN; empty or placeholder tokens are rejected.
- Do not expose port 8000 publicly. Docker binds it to 127.0.0.1 only.
- Do not enable Tor until a dedicated local web listener and operational checks are configured.
