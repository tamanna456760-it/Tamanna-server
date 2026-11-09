# Tamanna AI — production deployment guide

This repository contains the Tamanna AI API and the static public website in `Wabsite/`.
This guide documents deployment; it does not create a VPS, register a domain, configure Cloudflare, or deploy automatically.

## Canonical domain

- Public canonical website: `https://www.bd-king-r7.com/`
- Apex domain: `https://bd-king-r7.com/` must permanently redirect to the canonical www host.
- Cloudflare nameservers supplied for the zone: `pablo.ns.cloudflare.com` and `uma.ns.cloudflare.com`.

There is no legacy-domain alias in this configuration. Do not create duplicate www DNS records or duplicate Nginx server blocks.

## 1. Host and DNS prerequisites

Use an Ubuntu 22.04/24.04 VPS (or equivalent Linux host) with Docker Engine, Docker Compose, Nginx, and Certbot.

Create these Cloudflare DNS records only after confirming the real public origin address:

| Type | Name | Target |
|---|---|---|
| A | `@` | Actual VPS public IPv4 |
| CNAME | `www` | `bd-king-r7.com` |

Keep Cloudflare proxy enabled only after the origin and TLS configuration are correct. Do not publish a placeholder IP. Add AAAA records only if IPv6 works end-to-end.

Verify from an external network:
```sh
dig +short A bd-king-r7.com
dig +short A www.bd-king-r7.com
dig +short AAAA bd-king-r7.com
```

## 2. Private application configuration

```sh
git clone https://github.com/tamanna456760-it/Tamanna-server.git
cd Tamanna-server
cp .env.example .env
chmod 600 .env
openssl rand -hex 32
```

Set production values in the private `.env` file. At minimum:
- `APP_ENV=production`
- `APP_DEBUG=false`
- `ORCHESTRATOR_TOKEN=<unique-random-value>`
- `DATABASE_URL=sqlite:////app/data/reports.db`
- `CORS_ORIGINS=https://www.bd-king-r7.com,https://bd-king-r7.com`
- `TRUST_PROXY=true` only when the API is reachable exclusively through the trusted local Nginx proxy
- `MAX_CONTENT_LENGTH=1048576`
- `RATE_LIMIT_PER_MINUTE=60`

Never commit `.env`, API keys, database files, TLS certificates, or private keys.

## 3. Build and start

```sh
docker compose config
docker compose build --no-cache
docker compose up -d
docker compose ps
docker compose logs --tail=100 orchestrator
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/health/ready
```

The API should remain bound to host loopback and must not expose port 8000 publicly. Confirm the actual Compose service names in `docker compose config` before using service-specific log commands.

## 4. Nginx and TLS

First install the HTTP-only ACME bootstrap configuration:
```sh
sudo mkdir -p /var/www/html
sudo cp deploy/nginx/acme-bootstrap.conf /etc/nginx/sites-available/tamanna
sudo ln -sfn /etc/nginx/sites-available/tamanna /etc/nginx/sites-enabled/tamanna
sudo nginx -t
sudo systemctl reload nginx
```

After both apex and www DNS records resolve to this VPS, issue one certificate covering both hosts:
```sh
sudo certbot certonly --webroot -w /var/www/html -d bd-king-r7.com -d www.bd-king-r7.com
```

Install the production Nginx configuration:
```sh
sudo cp deploy/nginx/tamanna-domains.conf /etc/nginx/sites-available/tamanna
sudo nginx -t
sudo systemctl reload nginx
sudo certbot renew --dry-run
```

Ensure the Nginx document root points to the deployed `Wabsite/` directory. Confirm the API upstream and port match the actual Compose service before enabling the proxy.

## 5. Firewall and smoke tests

Allow SSH (restricted where possible), HTTP, and HTTPS. Do not expose port 8000:
```sh
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp
sudo ufw enable
```

After deployment:
```sh
curl -I https://www.bd-king-r7.com/
curl -I https://bd-king-r7.com/
curl --fail https://www.bd-king-r7.com/robots.txt
curl --fail https://www.bd-king-r7.com/sitemap.xml
curl --fail https://www.bd-king-r7.com/health
```

Expected: canonical www returns 200; apex returns a permanent redirect to `https://www.bd-king-r7.com/`; robots and sitemap return 200.

## 6. Google Search readiness

The public website must be reachable anonymously over HTTPS. Keep the homepage indexable, use one self-referencing canonical URL, and ensure the sitemap contains only canonical public URLs.

- Robots file: `https://www.bd-king-r7.com/robots.txt`
- Sitemap: `https://www.bd-king-r7.com/sitemap.xml`
- Canonical homepage: `https://www.bd-king-r7.com/`

After DNS and hosting are live, verify both apex and www domain properties in Google Search Console, submit the sitemap, and use URL Inspection to request indexing of the homepage. Search Console verification and submission require the domain owner's action.

## 7. Tests and operational limits

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt pytest
ORCHESTRATOR_TOKEN=local-test-token DATABASE_URL=sqlite:// pytest -q
python scripts/validate_json.py
python scripts/validate_domains.py
node --test Wabsite/seo.test.js
```

Back up the persistent data volume before upgrades and test restoration periodically. A passing CI run does not prove that DNS, TLS, the VPS, or production storage is healthy.

The current API is not a full user login/role-management platform. SQLite is intended for a small single-node deployment. Confirm the actual app runtime, service names, ports, and Nginx upstream before production rollout.


## 8. Automated Ubuntu VPS bootstrap (new)

The repository includes two scripts for the selected `bd-king-r7.com` + own-VPS deployment:

1. From a fresh Ubuntu 22.04/24.04 VPS, connect over SSH and run:
   ```sh
   git clone https://github.com/tamanna456760-it/Tamanna-server.git
   cd Tamanna-server
   sudo bash deploy/vps-setup.sh
   ```
   The script installs the host packages, clones/updates the app under `/var/www/tamanna`, creates a private `.env` with a random orchestrator token if one does not exist, starts Compose, and installs the HTTP ACME bootstrap Nginx site. It does not buy a domain or guess an IP address.

2. At the DNS provider, set the apex A record (`@`) and `www` A record to the VPS public IPv4. Wait until both resolve to that exact address.

3. Activate HTTPS:
   ```sh
   sudo bash /var/www/tamanna/deploy/enable-tls.sh
   ```
   The script checks both DNS names against the VPS public IPv4 before requesting a certificate, then installs the production Nginx config and tests renewal.

4. Verify:
   ```sh
   cd /var/www/tamanna
   docker compose ps
   curl --fail http://127.0.0.1:8000/health/ready
   curl --fail https://www.bd-king-r7.com/health/ready
   curl -I https://bd-king-r7.com/
   ```

Review your VPS provider's firewall/security-group rules as well as UFW. Permit inbound SSH on the actual SSH port, TCP 80 and TCP 443; do not permit public TCP 8000. Keep `.env` readable only by root and never paste its contents into chat or commit it. The bootstrap script must be reviewed against your provider's SSH port and firewall policy before running on a remote host.


## 9. GitHub Actions → VPS deployment

The manual workflow `.github/workflows/deploy-vps.yml` deploys the latest `main` commit to an already bootstrapped Ubuntu VPS. It does not create or rent a VPS, configure DNS, or enable TLS.

### One-time VPS setup

Complete sections 1–4 above and run `deploy/vps-setup.sh` once. Confirm the app exists at `/var/www/tamanna`, Docker Compose works, and the VPS SSH login is available. Keep the SSH port that was configured on the VPS.

### Add repository Actions secrets

In GitHub, open **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Value |
|---|---|
| `VPS_HOST` | VPS public IPv4 address or SSH hostname |
| `VPS_USER` | SSH user allowed to run the deployment commands (normally a dedicated deploy user with controlled Docker access) |
| `VPS_SSH_KEY` | Private key for that SSH user; never commit or paste it into the repository |
| `VPS_KNOWN_HOSTS` | Verified SSH host-key line for this host |
| `VPS_SSH_PORT` | Optional custom SSH TCP port; defaults to `22` |

Obtain the server host key from the VPS/provider console or another trusted channel and verify its fingerprint before saving it as `VPS_KNOWN_HOSTS`. For a non-default port, the known-hosts entry normally uses `[host]:port`. Do not disable SSH host-key checking.

### Run a deployment

Open **Actions → Deploy Tamanna API to VPS → Run workflow**, select `main`, and start the workflow. The job fetches and fast-forward updates `main`, validates the Compose configuration, rebuilds/restarts the services, and checks `http://127.0.0.1:8000/health/ready`. It fails rather than silently overwriting a non-fast-forward checkout or deploying when the initial VPS bootstrap is missing.

The workflow is manual-only: pushes to GitHub do not automatically change the production server. Review the Actions log after each run. Never add credentials to workflow YAML, source files, or committed `.env` files.
