# Tamanna Central Server deployment

## Requirements
- Ubuntu 22.04/24.04 VPS or another Docker-capable Linux host
- Docker Engine and Docker Compose plugin
- DNS A/AAAA record pointing the selected domain to the host
- Nginx or Caddy configured with a valid TLS certificate

## Configure
1. Copy `.env.example` to `.env`.
2. Generate a unique random `ORCHESTRATOR_TOKEN` on the server.
3. Keep `.env`, credentials, certificates, and private keys out of Git.
4. Review `DATABASE_URL` before production use.

## Start
```sh
docker compose config
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail=100 orchestrator
```

The service binds to 127.0.0.1:8000 on the host. Put a reverse proxy with TLS in front of it. Do not expose port 8000 directly to the public internet.

## Verify
```sh
curl --fail http://127.0.0.1:8000/health
```

Expected JSON: `{"status":"ok","service":"tamanna-central-server"}`.

This repository supplies deployment configuration and application code; it does not provision a VPS, DNS, or TLS certificates by itself.
