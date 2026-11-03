#!/usr/bin/env sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$ROOT"
if ! command -v docker >/dev/null 2>&1; then echo "ERROR: Docker is not installed." >&2; exit 1; fi
if ! docker compose version >/dev/null 2>&1; then echo "ERROR: Docker Compose plugin is required." >&2; exit 1; fi
if [ ! -f .env ]; then cp .env.example .env; echo "Created private .env"; fi
if ! grep -Eq '^ORCHESTRATOR_TOKEN=.{32,}$' .env; then
  TOKEN="$(python3 -c 'import secrets; print(secrets.token_hex(32))' 2>/dev/null || openssl rand -hex 32)"
  if grep -q '^ORCHESTRATOR_TOKEN=' .env; then sed "s|^ORCHESTRATOR_TOKEN=.*|ORCHESTRATOR_TOKEN=$TOKEN|" .env > .env.tmp; mv .env.tmp .env; else printf '\nORCHESTRATOR_TOKEN=%s\n' "$TOKEN" >> .env; fi
  echo "Generated private ORCHESTRATOR_TOKEN in .env"
fi
chmod 600 .env 2>/dev/null || true
docker compose up --build -d
docker compose ps
echo "Website: http://127.0.0.1:3000"
echo "API health: http://127.0.0.1:8000/health"
echo "API readiness: http://127.0.0.1:8000/health/ready"
echo "If a service is not healthy: docker compose logs --tail=150"
