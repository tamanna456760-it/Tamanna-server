# Tamanna Central Server — deployment guide

This repository contains a Flask API and a static website at `Wabsite/Index.html`. It does not create a VPS, control Cloudflare, issue certificates, or deploy itself.

## 1. Prerequisites

- Registered `bd-king-r7.com` domain and registrar access.
- Cloudflare zone set to **Active** (not Pending).
- Ubuntu VPS, Docker Engine, Docker Compose, Nginx, and Certbot.
- A real public IPv4 address for the origin.
- Firewall allows inbound TCP 80/443; port 8000 remains private.

## 2. Cloudflare DNS

Use the nameservers assigned in the user's Cloudflare dashboard:
- `pablo.ns.cloudflare.com`
- `uma.ns.cloudflare.com`

At the registrar, replace all previous nameservers with those two values. Wait until Cloudflare Overview shows **Active**. Then add these DNS records in Cloudflare:

| Type | Name | Content | Proxy |
|---|---|---|---|
| A | @ | REAL_ORIGIN_PUBLIC_IPV4 | Proxied |
| CNAME | www | bd-king-r7.com | Proxied |

Do not enter the placeholder string as an IP. Do not create email MX/SPF/DKIM/DMARC records until an actual mail provider is selected. The repository file `domains/cloudflare-dns-records.json` documents the intended records; it does not call Cloudflare's API.

Verify after DNS activation:
```sh
dig +short A bd-king-r7.com
dig +short A www.bd-king-r7.com
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

## 4. Issue origin TLS

After both hostnames resolve to the VPS:
```sh
sudo mkdir -p /var/www/html
sudo cp deploy/nginx/acme-bootstrap.conf /etc/nginx/sites-available/tamanna
sudo ln -sfn /etc/nginx/sites-available/tamanna /etc/nginx/sites-enabled/tamanna
sudo nginx -t && sudo systemctl reload nginx
sudo certbot certonly --webroot -w /var/www/html -d bd-king-r7.com -d www.bd-king-r7.com
sudo cp deploy/nginx/tamanna-domains.conf /etc/nginx/sites-available/tamanna
sudo nginx -t && sudo systemctl reload nginx
sudo certbot renew --dry-run
```

Set Cloudflare SSL/TLS encryption mode to **Full (strict)** only after the origin certificate is installed and valid. Do not enable HSTS preload or includeSubDomains until every affected hostname is HTTPS-ready.

## 5. Build, run, and verify

```sh
docker compose config
docker compose build --no-cache
docker compose up -d
docker compose ps
curl --fail http://127.0.0.1:8000/health
curl --fail https://www.bd-king-r7.com/health
curl --fail https://www.bd-king-r7.com/health/ready
```

Run tests before deployment:
```sh
python scripts/validate_json.py
python scripts/validate_domains.py
python -m pytest -q
```

A green CI run validates repository checks only. It does not prove domain registration, Cloudflare activation, live DNS, origin TLS, VPS availability, or production deployment.
