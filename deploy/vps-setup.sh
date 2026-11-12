#!/usr/bin/env bash
set -Eeuo pipefail
REPO_URL="https://github.com/tamanna456760-it/Tamanna-server.git"
AI_REPO_URL="https://github.com/tamanna456760-it/Tamanna-.git"
APP_DIR="/var/www/tamanna"
AI_DIR="$APP_DIR/vendor/tamanna-ai"
if [[ "$EUID" -ne 0 ]]; then echo "Run as root: sudo bash deploy/vps-setup.sh" >&2; exit 1; fi
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl git nginx certbot python3-certbot-nginx ufw openssl
if ! command -v docker >/dev/null 2>&1; then apt-get install -y docker.io docker-compose-v2; fi
systemctl enable --now docker
systemctl enable --now nginx
if [[ -d "$APP_DIR/.git" ]]; then
  git -C "$APP_DIR" fetch --prune origin main
  git -C "$APP_DIR" merge --ff-only origin/main
elif [[ -e "$APP_DIR" ]]; then
  echo "Refusing to overwrite non-Git directory: $APP_DIR" >&2; exit 1
else
  git clone --branch main --depth 1 "$REPO_URL" "$APP_DIR"
fi
mkdir -p "$APP_DIR/vendor"
if [[ -d "$AI_DIR/.git" ]]; then
  git -C "$AI_DIR" fetch --prune origin main
  git -C "$AI_DIR" merge --ff-only origin/main
elif [[ -e "$AI_DIR" ]]; then
  echo "Refusing to overwrite non-Git AI directory: $AI_DIR" >&2; exit 1
else
  git clone --branch main --depth 1 "$AI_REPO_URL" "$AI_DIR"
fi
test -f "$AI_DIR/Main.py"
test -f "$AI_DIR/requirements-server.txt"
cd "$APP_DIR"
if [[ ! -f .env ]]; then install -m 600 .env.example .env; fi
chmod 600 .env
if ! grep -Eq '^ORCHESTRATOR_TOKEN=.{32,}$' .env; then
  TOKEN="$(openssl rand -hex 32)"
  if grep -q '^ORCHESTRATOR_TOKEN=' .env; then sed -i "s|^ORCHESTRATOR_TOKEN=.*|ORCHESTRATOR_TOKEN=$TOKEN|" .env
  else printf '\nORCHESTRATOR_TOKEN=%s\n' "$TOKEN" >> .env; fi
  unset TOKEN
fi
if ! grep -Eq '^TAMANNA_SESSION_SECRET=.{32,}$' .env; then
  SESSION_SECRET="$(openssl rand -hex 32)"
  if grep -q '^TAMANNA_SESSION_SECRET=' .env; then sed -i "s|^TAMANNA_SESSION_SECRET=.*|TAMANNA_SESSION_SECRET=$SESSION_SECRET|" .env
  else printf '\nTAMANNA_SESSION_SECRET=%s\n' "$SESSION_SECRET" >> .env; fi
  unset SESSION_SECRET
fi
set_env() {
  key="$1"; value="$2"
  if grep -q "^$key=" .env; then sed -i "s|^$key=.*|$key=$value|" .env
  else printf '\n%s=%s\n' "$key" "$value" >> .env; fi
}
set_env APP_ENV production
set_env APP_DEBUG false
set_env TRUST_PROXY true
set_env CORS_ORIGINS "https://www.bd-king-r7.com,https://bd-king-r7.com"
chmod 600 .env
docker compose config --quiet
docker compose --profile ai up -d --build
install -d -m 755 /var/www/html
install -m 644 deploy/nginx/acme-bootstrap.conf /etc/nginx/sites-available/tamanna
ln -sfn /etc/nginx/sites-available/tamanna /etc/nginx/sites-enabled/tamanna
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
if command -v sshd >/dev/null 2>&1; then
  SSH_PORT="$(sshd -T 2>/dev/null | awk '$1 == "port" { print $2; exit }')"
  if [[ "$SSH_PORT" =~ ^[0-9]+$ ]] && (( SSH_PORT >= 1 && SSH_PORT <= 65535 )); then
    ufw allow "$SSH_PORT/tcp"; ufw allow 80/tcp; ufw allow 443/tcp; ufw --force enable
  else echo "Could not determine SSH port; leaving UFW unchanged." >&2; fi
else echo "sshd not found; leaving UFW unchanged." >&2; fi
echo "Bootstrap completed. Verify: docker compose ps"
curl --fail --silent --show-error http://127.0.0.1:8000/health
curl --fail --silent --show-error http://127.0.0.1:8001/health
echo
echo "Point DNS A records @ and www to this VPS, then run:"
echo "sudo bash $APP_DIR/deploy/enable-tls.sh"
echo "Do not expose TCP/8000 or TCP/8001 publicly. Keep .env private."
