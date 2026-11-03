# Tamanna Central Server deployment

## Requirements
- Ubuntu 22.04/24.04 VPS or another Docker-capable Linux host
- Docker Engine and Docker Compose plugin
- DNS A/AAAA record pointing the selected domain to the host
- Nginx or Caddy configured with a valid TLS certificate

## Configure
1. Copy `.env.example` to `.env`.
2. Generate a unique random `ORCHESTRATOR_TOKEN` on the server (for example, `openssl rand -hex 32`).
3. Keep `.env`, credentials, certificates, and private keys out of Git.
4. Review `DATABASE_URL` before production use. The Compose default stores SQLite data in the persistent `tamanna-data` volume.

## Start
```sh
docker compose config
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail=100 orchestrator
```

The service binds to 127.0.0.1:8000 on the host. Put a reverse proxy with TLS in front of it. Do not expose port 8000 directly to the public internet.

## API authentication
- `GET /health` is a minimal unauthenticated liveness check.
- `POST /api/report` requires `Authorization: Bearer $ORCHESTRATOR_TOKEN`.
- `GET /api/reports` requires the same bearer token.
- `GET /` returns only non-sensitive service metadata; it never lists stored reports.

Example:
```sh
curl --fail http://127.0.0.1:8000/health
curl --fail -H "Authorization: Bearer $ORCHESTRATOR_TOKEN" \
  http://127.0.0.1:8000/api/reports
```

## Verify
Expected health JSON: `{"status":"ok","service":"tamanna-central-server"}`.

Run the automated tests with:
```sh
python -m pip install -r requirements.txt pytest
ORCHESTRATOR_TOKEN=local-test-token DATABASE_URL=sqlite:// pytest -q
```

This repository supplies deployment configuration and application code; it does not provision a VPS, DNS, or TLS certificates by itself.
