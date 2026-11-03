#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Missing .env. Run: cp .env.example .env"
  echo "Then generate ORCHESTRATOR_TOKEN with: python3 -c 'import secrets; print(secrets.token_urlsafe(48))'"
  exit 1
fi

python3 scripts/server_preflight.py
mkdir -p data
chmod 700 data
docker compose config --quiet
docker compose up -d --build
docker compose ps
echo "Waiting for health endpoint..."
for attempt in $(seq 1 30); do
  if curl --fail --silent http://127.0.0.1:8000/health; then
    echo
    echo "Tamanna orchestrator is healthy on http://127.0.0.1:8000"
    exit 0
  fi
  sleep 2
done

echo "Health check failed. Recent logs:"
docker compose logs --tail=100 orchestrator
exit 1
