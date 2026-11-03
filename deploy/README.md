# Tamanna Central Server — deployment guide

This repository contains a Flask API and a static website source at `Wabsite/Index.html`.
It does **not** create a VPS, control DNS, issue certificates, or deploy itself.

## 1. Host prerequisites

- Ubuntu 22.04/24.04 VPS (or equivalent Linux host)
- Docker Engine with the Docker Compose plugin
- Nginx and Certbot
- DNS for `bd-king-r7.com` and `www.bd-king-r7.com` pointing to this VPS; retain `www.tamanna.com` DNS pointing to the same origin for the legacy redirect
- Firewall allowing inbound TCP 80 and 443; do not expose 8000 publicly

Verify DNS before proceeding:
```sh
dig +short A bd-king-r7.com
dig +short A www.bd-king-r7.com
dig +short A www.tamanna.com
```
If the VPS uses IPv6, configure matching AAAA records only when IPv6 is working end-to-end.

## 2. Domain and Cloudflare DNS

The canonical website is `https://www.bd-king-r7.com`. Keep `www.tamanna.com` as a legacy alias that redirects to it. The `bd-king-r7.com` zone uses the Cloudflare nameservers assigned in the dashboard: `pablo.ns.cloudflare.com` and `uma.ns.cloudflare.com`. The separate `tamanna.com` DNS zone must also keep `www` pointed at this origin. A valid TLS certificate for `www.tamanna.com` is required before the HTTPS redirect can work. Do not publish a placeholder IP; use the real public IPv4 of the VPS.

## 3. Configure the application

```sh
git clone https://github.com/tamanna456760-it/Tamanna-server.git
cd Tamanna-server
cp .env.example .env
chmod 600 .env
```

Generate a private token on the VPS and add it to `.env`:
```sh
openssl rand -hex 32
```

Set at least (replace the values with your actual production configuration):
- `APP_ENV=production`
- `APP_DEBUG=false`
- `ORCHESTRATOR_TOKEN=<unique-random-value>`
- `DATABASE_URL=sqlite:////app/data/reports.db`
- `CORS_ORIGINS=https://bd-king-r7.com,https://www.bd-king-r7.com` (do not allow `*`; the legacy hostname only redirects)
- `TRUST_PROXY=true` only when the API is reachable exclusively through the local trusted Nginx reverse proxy
- `MAX_CONTENT_LENGTH=1048576`
- `RATE_LIMIT_PER_MINUTE=60`
- `RATE_LIMIT_PER_MINUTE=60`

Keep `.env`, API keys, database files, TLS certificates, and private keys out of GitHub. Never paste a real token into an issue, chat, workflow file, or commit.

## 4. Build and start the API

```sh
docker compose config
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose logs --tail=100 orchestrator
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/health/ready
```

Compose binds the API to host loopback `127.0.0.1:8000`. Keep it behind Nginx. The named `tamanna-data` volume stores the SQLite database.

## 5. Issue TLS certificates

First install the temporary HTTP-only config:
```sh
sudo mkdir -p /var/www/html
sudo cp deploy/nginx/acme-bootstrap.conf /etc/nginx/sites-available/tamanna
sudo ln -sfn /etc/nginx/sites-available/tamanna /etc/nginx/sites-enabled/tamanna
sudo nginx -t
sudo systemctl reload nginx
```

After the new canonical hosts and retained legacy alias resolve to this server, issue certificates:
```sh
sudo certbot certonly --webroot -w /var/www/html -d bd-king-r7.com -d www.bd-king-r7.com
sudo certbot certonly --webroot -w /var/www/html --cert-name www.tamanna.com -d www.tamanna.com
```

Then install the production TLS virtual hosts:
```sh
sudo cp deploy/nginx/tamanna-domains.conf /etc/nginx/sites-available/tamanna
sudo nginx -t
sudo systemctl reload nginx
sudo certbot renew --dry-run
```

The Nginx configuration serves the website from `/var/www/tamanna/Wabsite`. Copy the repository's `Wabsite` directory to that path (or change the Nginx root to the actual deployment path). The API proxy preserves the `/api/` prefix.

## 6. Firewall and verification

Allow only SSH (restricted to trusted IPs where possible), HTTP, and HTTPS. Example with UFW:
```sh
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp
sudo ufw enable
```

Verify from the server and an external network:
```sh
curl -I https://www.bd-king-r7.com/
curl --fail https://www.bd-king-r7.com/health
curl --fail https://www.bd-king-r7.com/health/ready
curl -I https://www.tamanna.com/  # expected: 301 to https://www.bd-king-r7.com/
```

The health endpoints are public and intentionally return minimal information. API routes require:
```sh
curl --fail -H "Authorization: Bearer $ORCHESTRATOR_TOKEN" \
  https://www.bd-king-r7.com/api/reports
```

## 7. Tests and maintenance

Run local tests before deploying:
```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt pytest
ORCHESTRATOR_TOKEN=local-test-token DATABASE_URL=sqlite:// pytest -q
python scripts/validate_json.py
python scripts/validate_domains.py
```

Back up the `tamanna-data` volume before upgrades. Test restore procedures periodically. Review logs for errors, keep the host and dependencies patched, and rotate the bearer token if it may have been exposed.

## Current limitations

- The report API has bearer-token authentication, input validation, request-size limits, security headers, CORS allowlisting, and a per-process rate limit. For multi-worker or multi-instance deployments, enforce distributed rate limits at the reverse proxy/WAF.
- The current API is not a full user login system or role-based admin platform.
- SQLite is suitable for a small single-node deployment; choose and test a managed PostgreSQL database before scaling horizontally.
- Backup automation, restore verification, alert delivery, and production deployment automation are not provided by this Compose file.
- A green CI run does not prove the live domain, DNS, TLS, VPS, or production database is healthy.

Never deploy until DNS, TLS, host firewall, secrets, and an actual restore test have been verified.
