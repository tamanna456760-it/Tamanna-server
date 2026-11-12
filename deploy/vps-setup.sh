#!/usr/bin/env bash
set -Eeuo pipefail

# First-time Ubuntu 22.04/24.04 VPS bootstrap for bd-king-r7.com.
# Run as root: bash deploy/vps-setup.sh
DOMAIN="bd-king-r7.com"
REPO_URL="https://github.com/tamanna456760-it/Tamanna-server.git"
APP_DIR="/var/www/tamanna"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo bash deploy/vps-setup.sh" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl git nginx certbot python3-certbot-nginx ufw openssl

# Install Docker Engine from Ubuntu packages when it is not already available.
if ! command -v docker >/dev/null 2>&1; then
  apt-get install -y docker.io docker-compose-v2
fi
systemctl enable --now docker
systemctl enable --now nginx

if [[ -d "${APP_DIR}/.git" ]]; then
  git -C "${APP_DIR}" pull --ff-only origin main
elif [[ -e "${APP_DIR}" ]]; then
  echo "Refusing to overwrite non-Git directory: ${APP_DIR}" >&2
  exit 1
else
  git clone --branch main --depth 1 "${REPO_URL}" "${APP_DIR}"
fi

cd "${APP_DIR}"
if [[ ! -f .env ]]; then
  install -m 600 .env.example .env
  TOKEN="$(openssl rand -hex 32)"
  sed -i "s/^ORCHESTRATOR_TOKEN=.*/ORCHESTRATOR_TOKEN=${TOKEN}/" .env
  unset TOKEN
fi
chmod 600 .env

# Generate the session-signing secret once; never print or commit it.
if ! grep -Eq '^TAMANNA_SESSION_SECRET=.{32,}$' .env; then
  SESSION_SECRET="$(openssl rand -hex 32)"
  if grep -q '^TAMANNA_SESSION_SECRET=' .env; then
    sed -i "s|^TAMANNA_SESSION_SECRET=.*|TAMANNA_SESSION_SECRET=\${SESSION_SECRET}|" .env
  else
    printf '\nTAMANNA_SESSION_SECRET=%s\n' "\${SESSION_SECRET}" >> .env
  fi
  unset SESSION_SECRET
fi

# Enforce safe production defaults without printing secrets.
sed -i 's/^APP_ENV=.*/APP_ENV=production/' .env
sed -i 's/^APP_DEBUG=.*/APP_DEBUG=false/' .env
sed -i 's/^TRUST_PROXY=.*/TRUST_PROXY=true/' .env
sed -i 's|^CORS_ORIGINS=.*|CORS_ORIGINS=https://www.bd-king-r7.com,https://bd-king-r7.com|' .env

if ! grep -Eq '^ORCHESTRATOR_TOKEN=.{32,}$' .env; then
  echo "ORCHESTRATOR_TOKEN is missing/too short. Set a random 32+ character token in \${APP_DIR}/.env" >&2
  exit 1
fi

# API is bound to loopback by Compose; only Nginx is exposed publicly.
docker compose config >/dev/null
docker compose --profile ai up -d --build
install -d -m 755 /var/www/html
install -m 644 deploy/nginx/acme-bootstrap.conf /etc/nginx/sites-available/tamanna
ln -sfn /etc/nginx/sites-available/tamanna /etc/nginx/sites-enabled/tamanna
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# Detect the active SSH daemon port before enabling UFW to avoid locking out
# VPS providers that use a non-standard SSH port.
if command -v sshd >/dev/null 2>&1; then
  SSH_PORT="$(sshd -T 2>/dev/null | awk '$1 == "port" { print $2; exit }')"
  if [[ "${SSH_PORT}" =~ ^[0-9]+$ ]] && (( SSH_PORT >= 1 && SSH_PORT <= 65535 )); then
    ufw allow "${SSH_PORT}/tcp"
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
  else
    echo "Could not determine SSH port; leaving UFW unchanged to avoid lockout." >&2
  fi
else
  echo "sshd not found; leaving UFW unchanged. Configure provider firewall and UFW manually." >&2
fi

echo
echo "Bootstrap finished. Check: docker compose ps"
echo "Local API health:"
curl --fail --silent http://127.0.0.1:8000/health
curl --fail --silent http://127.0.0.1:8001/health
echo
echo "NEXT: point DNS A records @ and www to this VPS IPv4, then run:"
echo "  sudo bash ${APP_DIR}/deploy/enable-tls.sh"
echo "Do not expose TCP/8000 publicly. Keep .env private."
 .env; then
  SESSION_SECRET="$(openssl rand -hex 32)"
  if grep -q '^TAMANNA_SESSION_SECRET=' .env; then
    sed -i "s|^TAMANNA_SESSION_SECRET=.*|TAMANNA_SESSION_SECRET=${SESSION_SECRET}|" .env
  else
    printf '\nTAMANNA_SESSION_SECRET=%s\n' "${SESSION_SECRET}" >> .env
  fi
  unset SESSION_SECRET
fi

# Enforce safe production defaults without printing secrets.
sed -i 's/^APP_ENV=.*/APP_ENV=production/' .env
sed -i 's/^APP_DEBUG=.*/APP_DEBUG=false/' .env
sed -i 's/^TRUST_PROXY=.*/TRUST_PROXY=true/' .env
sed -i 's|^CORS_ORIGINS=.*|CORS_ORIGINS=https://www.bd-king-r7.com,https://bd-king-r7.com|' .env

if ! grep -q '^ORCHESTRATOR_TOKEN=.{32,}$' .env; then
  echo "ORCHESTRATOR_TOKEN is missing/too short. Set a random 32+ character token in ${APP_DIR}/.env" >&2
  exit 1
fi

# API is bound to loopback by Compose; only Nginx is exposed publicly.
docker compose config >/dev/null
docker compose --profile ai up -d --build
install -d -m 755 /var/www/html
install -m 644 deploy/nginx/acme-bootstrap.conf /etc/nginx/sites-available/tamanna
ln -sfn /etc/nginx/sites-available/tamanna /etc/nginx/sites-enabled/tamanna
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# Detect the active SSH daemon port before enabling UFW to avoid locking out
# VPS providers that use a non-standard SSH port.
if command -v sshd >/dev/null 2>&1; then
  SSH_PORT="$(sshd -T 2>/dev/null | awk '$1 == "port" { print $2; exit }')"
  if [[ "${SSH_PORT}" =~ ^[0-9]+$ ]] && (( SSH_PORT >= 1 && SSH_PORT <= 65535 )); then
    ufw allow "${SSH_PORT}/tcp"
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
  else
    echo "Could not determine SSH port; leaving UFW unchanged to avoid lockout." >&2
  fi
else
  echo "sshd not found; leaving UFW unchanged. Configure provider firewall and UFW manually." >&2
fi

echo
echo "Bootstrap finished. Check: docker compose ps"
echo "Local API health:"
curl --fail --silent http://127.0.0.1:8000/health
curl --fail --silent http://127.0.0.1:8001/health
echo
echo "NEXT: point DNS A records @ and www to this VPS IPv4, then run:"
echo "  sudo bash ${APP_DIR}/deploy/enable-tls.sh"
echo "Do not expose TCP/8000 publicly. Keep .env private."
 .env; then
  echo "ORCHESTRATOR_TOKEN is missing/too short. Set a random 32+ character token in ${APP_DIR}/.env" >&2
  exit 1
fi

# API is bound to loopback by Compose; only Nginx is exposed publicly.
docker compose config >/dev/null
docker compose --profile ai up -d --build
install -d -m 755 /var/www/html
install -m 644 deploy/nginx/acme-bootstrap.conf /etc/nginx/sites-available/tamanna
ln -sfn /etc/nginx/sites-available/tamanna /etc/nginx/sites-enabled/tamanna
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# Detect the active SSH daemon port before enabling UFW to avoid locking out
# VPS providers that use a non-standard SSH port.
if command -v sshd >/dev/null 2>&1; then
  SSH_PORT="$(sshd -T 2>/dev/null | awk '$1 == "port" { print $2; exit }')"
  if [[ "${SSH_PORT}" =~ ^[0-9]+$ ]] && (( SSH_PORT >= 1 && SSH_PORT <= 65535 )); then
    ufw allow "${SSH_PORT}/tcp"
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
  else
    echo "Could not determine SSH port; leaving UFW unchanged to avoid lockout." >&2
  fi
else
  echo "sshd not found; leaving UFW unchanged. Configure provider firewall and UFW manually." >&2
fi

echo
echo "Bootstrap finished. Check: docker compose ps"
echo "Local API health:"
curl --fail --silent http://127.0.0.1:8000/health
curl --fail --silent http://127.0.0.1:8001/health
echo
echo "NEXT: point DNS A records @ and www to this VPS IPv4, then run:"
echo "  sudo bash ${APP_DIR}/deploy/enable-tls.sh"
echo "Do not expose TCP/8000 publicly. Keep .env private."
 .env; then
  SESSION_SECRET="$(openssl rand -hex 32)"
  if grep -q '^TAMANNA_SESSION_SECRET=' .env; then
    sed -i "s|^TAMANNA_SESSION_SECRET=.*|TAMANNA_SESSION_SECRET=${SESSION_SECRET}|" .env
  else
    printf '\nTAMANNA_SESSION_SECRET=%s\n' "${SESSION_SECRET}" >> .env
  fi
  unset SESSION_SECRET
fi

# Enforce safe production defaults without printing secrets.
sed -i 's/^APP_ENV=.*/APP_ENV=production/' .env
sed -i 's/^APP_DEBUG=.*/APP_DEBUG=false/' .env
sed -i 's/^TRUST_PROXY=.*/TRUST_PROXY=true/' .env
sed -i 's|^CORS_ORIGINS=.*|CORS_ORIGINS=https://www.bd-king-r7.com,https://bd-king-r7.com|' .env

if ! grep -q '^ORCHESTRATOR_TOKEN=.{32,}$' .env; then
  echo "ORCHESTRATOR_TOKEN is missing/too short. Set a random 32+ character token in ${APP_DIR}/.env" >&2
  exit 1
fi

# API is bound to loopback by Compose; only Nginx is exposed publicly.
docker compose config >/dev/null
docker compose --profile ai up -d --build
install -d -m 755 /var/www/html
install -m 644 deploy/nginx/acme-bootstrap.conf /etc/nginx/sites-available/tamanna
ln -sfn /etc/nginx/sites-available/tamanna /etc/nginx/sites-enabled/tamanna
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# Detect the active SSH daemon port before enabling UFW to avoid locking out
# VPS providers that use a non-standard SSH port.
if command -v sshd >/dev/null 2>&1; then
  SSH_PORT="$(sshd -T 2>/dev/null | awk '$1 == "port" { print $2; exit }')"
  if [[ "${SSH_PORT}" =~ ^[0-9]+$ ]] && (( SSH_PORT >= 1 && SSH_PORT <= 65535 )); then
    ufw allow "${SSH_PORT}/tcp"
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
  else
    echo "Could not determine SSH port; leaving UFW unchanged to avoid lockout." >&2
  fi
else
  echo "sshd not found; leaving UFW unchanged. Configure provider firewall and UFW manually." >&2
fi

echo
echo "Bootstrap finished. Check: docker compose ps"
echo "Local API health:"
curl --fail --silent http://127.0.0.1:8000/health
curl --fail --silent http://127.0.0.1:8001/health
echo
echo "NEXT: point DNS A records @ and www to this VPS IPv4, then run:"
echo "  sudo bash ${APP_DIR}/deploy/enable-tls.sh"
echo "Do not expose TCP/8000 publicly. Keep .env private."
