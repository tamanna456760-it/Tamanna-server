# Tamanna Central Server — deployment guide

This repository contains a Flask API and a static website at `Wabsite/Index.html`. It does not create a VPS, control Cloudflare, issue certificates, or deploy itself.

## 1. Prerequisites

- Registered `bd-king-r7.com` domain and registrar access.
- The `bd-king-r7.com` Cloudflare zone must show **Active**.
- The separate `tamanna.com` DNS zone must remain active for the legacy `www.tamanna.com` redirect.
- Ubuntu VPS, Docker Engine, Docker Compose, Nginx, and Certbot.
- A real public IPv4 address for the origin.
- Firewall allows inbound TCP 80/443; port 8000 remains private.

## 2. Cloudflare DNS

For `bd-king-r7.com`, use the nameservers assigned in the Cloudflare dashboard:
- `pablo.ns.cloudflare.com`
- `uma.ns.cloudflare.com`

At the registrar for `bd-king-r7.com`, set those nameservers and wait until Cloudflare Overview shows **Active**. Then add:

| Type | Name | Content | Proxy |
|---|---|---|---|
| A | @ | REAL_ORIGIN_PUBLIC_IPV4 | Proxied |
| CNAME | www | bd-king-r7.com | Proxied |

For the separate `tamanna.com` zone, keep `www` pointed to the same origin (A record with the real origin IPv4, or CNAME to a hostname that resolves to that origin). Do not remove its DNS or nameserver configuration. This repository does not know which nameservers currently serve `tamanna.com`.

Do not enter a placeholder as an IP. Do not create email MX/SPF/DKIM/DMARC records until an actual mail provider is selected. The JSON file documents intended DNS records; it does not call Cloudflare's API.

Verify DNS before issuing certificates:
```sh
dig +short A bd-king-r7.com
dig +short A www.bd-king-r7.com
dig +short A www.tamanna.com
```

## 3. Configure the application

```sh
git clone https://github.com/tamanna456760-it/Tamanna-server.git
cd Tamanna-server
cp .env.example .env
chmod 600 .env
openssl rand -hex 32
```

Set a unique generated `ORCHESTRATOR_TOKEN`, production mode, and:
```env
APP_ENV=production
APP_DEBUG=false
ORCHESTRATOR_TOKEN=REPLACE_WITH_UNIQUE_RANDOM_SECRET
DATABASE_URL=sqlite:////app/data/reports.db
CORS_ORIGINS=https://bd-king-r7.com,https://www.bd-king-r7.com
TRUST_PROXY=true
```
Keep `.env`, API keys, database files, TLS certificates, and private keys out of GitHub.

## 4. Issue TLS certificates and install Nginx

The old hostname uses HTTPS before it can redirect. A valid certificate for `www.tamanna.com` is therefore required; an HTTP redirect alone cannot fix an invalid TLS certificate.

Install the temporary HTTP config after all three hostnames resolve to this VPS:
```sh
sudo mkdir -p /var/www/html
sudo cp deploy/nginx/acme-bootstrap.conf /etc/nginx/sites-available/tamanna
sudo ln -sfn /etc/nginx/sites-available/tamanna /etc/nginx/sites-enabled/tamanna
sudo nginx -t && sudo systemctl reload nginx
sudo certbot certonly --webroot -w /var/www/html -d bd-king-r7.com -d www.bd-king-r7.com
sudo certbot certonly --webroot -w /var/www/html --cert-name www.tamanna.com -d www.tamanna.com
sudo cp deploy/nginx/tamanna-domains.conf /etc/nginx/sites-available/tamanna
sudo nginx -t && sudo systemctl reload nginx
sudo certbot renew --dry-run
```

Set Cloudflare SSL/TLS encryption mode to **Full (strict)** only after valid origin certificates are installed. Do not enable HSTS preload or includeSubDomains until every affected hostname is HTTPS-ready.

## 5. Build, run, and verify

```sh
docker compose config
docker compose build --no-cache
docker compose up -d
docker compose ps
curl --fail http://127.0.0.1:8000/health
curl --fail https://www.bd-king-r7.com/health
curl --fail -I https://www.tamanna.com/
curl --fail https://www.bd-king-r7.com/health/ready
```

The `www.tamanna.com` request should return a 301 redirect to `https://www.bd-king-r7.com/`.

Run tests before deployment:
```sh
python scripts/validate_json.py
python scripts/validate_domains.py
python -m pytest -q
```

A green CI run validates repository checks only. It does not prove domain registration, Cloudflare activation, live DNS, origin TLS, VPS availability, or production deployment.
