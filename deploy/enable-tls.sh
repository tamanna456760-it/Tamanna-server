#!/usr/bin/env bash
set -Eeuo pipefail

DOMAIN="bd-king-r7.com"
WWW="www.bd-king-r7.com"
APP_DIR="/var/www/tamanna"
WEBROOT="/var/www/html"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo bash deploy/enable-tls.sh" >&2
  exit 1
fi
if [[ ! -d "${APP_DIR}/.git" ]]; then
  echo "App not found at ${APP_DIR}; run deploy/vps-setup.sh first." >&2
  exit 1
fi
command -v certbot >/dev/null 2>&1 || { echo "Certbot is not installed." >&2; exit 1; }

PUBLIC_IP="$(curl -4fsS --max-time 10 https://api.ipify.org)"
for host in "${DOMAIN}" "${WWW}"; do
  if ! getent ahostsv4 "${host}" | awk '{print $1}' | grep -Fxq "${PUBLIC_IP}"; then
    echo "DNS for ${host} does not resolve to this VPS IPv4 (${PUBLIC_IP}). Fix DNS first." >&2
    exit 1
  fi
done

certbot certonly --non-interactive --agree-tos --register-unsafely-without-email \
  --webroot -w "${WEBROOT}" -d "${DOMAIN}" -d "${WWW}"

install -m 644 "${APP_DIR}/deploy/nginx/tamanna-domains.conf" /etc/nginx/sites-available/tamanna
nginx -t
systemctl reload nginx
certbot renew --dry-run

echo "TLS enabled. Verify https://${WWW}/ and https://${DOMAIN}/"
