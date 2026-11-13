#!/usr/bin/env bash
# Run from Kali Linux (SSH client) to bootstrap/update Tamanna on an Ubuntu VPS.
set -Eeuo pipefail

REPO_URL="https://github.com/tamanna456760-it/Tamanna-server.git"
REMOTE_SETUP="deploy/vps-setup.sh"

for cmd in ssh ssh-keygen; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "Missing $cmd. Install with: sudo apt update && sudo apt install -y openssh-client" >&2
    exit 1
  }
done

read -r -p "Ubuntu VPS IP or hostname: " VPS_HOST
read -r -p "SSH username: " VPS_USER
read -r -p "SSH port [22]: " VPS_PORT
VPS_PORT="${VPS_PORT:-22}"

[[ -n "$VPS_HOST" && -n "$VPS_USER" ]] || {
  echo "Host and username are required." >&2
  exit 1
}
[[ "$VPS_PORT" =~ ^[0-9]+$ ]] && (( VPS_PORT >= 1 && VPS_PORT <= 65535 )) || {
  echo "Invalid SSH port." >&2
  exit 1
}

SSH_DIR="$HOME/.ssh"
KEY_FILE="$SSH_DIR/tamanna_vps_ed25519"
mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

if [[ ! -f "$KEY_FILE" ]]; then
  echo "Creating a dedicated SSH key. Keep the private key on this Kali device."
  ssh-keygen -t ed25519 -a 64 -C "tamanna-kali-deploy" -f "$KEY_FILE"
fi
chmod 600 "$KEY_FILE"
chmod 644 "$KEY_FILE.pub"

echo
echo "Add this PUBLIC key to the VPS user's ~/.ssh/authorized_keys using the VPS provider console:"
cat "$KEY_FILE.pub"
echo
read -r -p "After adding the public key, press Enter to test SSH (Ctrl+C to stop): "

SSH_OPTS=(
  -p "$VPS_PORT"
  -i "$KEY_FILE"
  -o IdentitiesOnly=yes
  -o PreferredAuthentications=publickey
  -o ConnectTimeout=15
  -o StrictHostKeyChecking=ask
)

echo "Testing SSH connection..."
ssh "${SSH_OPTS[@]}" "$VPS_USER@$VPS_HOST" 'printf "SSH connection OK: "; hostname; . /etc/os-release; printf "OS: %s\n" "$PRETTY_NAME"; test "$ID" = ubuntu'

echo
echo "Starting Tamanna server bootstrap/update on the Ubuntu VPS..."
ssh -tt "${SSH_OPTS[@]}" "$VPS_USER@$VPS_HOST" 'REPO_URL="https://github.com/tamanna456760-it/Tamanna-server.git" REMOTE_SETUP="deploy/vps-setup.sh" bash -s' <<'REMOTE'
set -Eeuo pipefail

if [[ ! -r /etc/os-release ]]; then
  echo "Cannot identify remote operating system." >&2
  exit 1
fi
. /etc/os-release
if [[ "$ID" != "ubuntu" ]]; then
  echo "This deployment script requires Ubuntu; detected: $PRETTY_NAME" >&2
  exit 1
fi

if ! command -v sudo >/dev/null 2>&1; then
  echo "sudo is required on the VPS. Install/configure it first." >&2
  exit 1
fi

sudo apt-get update
sudo apt-get install -y git ca-certificates

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT
git clone --depth 1 --branch main "$REPO_URL" "$WORK_DIR/Tamanna-server"
test -s "$WORK_DIR/Tamanna-server/$REMOTE_SETUP"
sudo bash "$WORK_DIR/Tamanna-server/$REMOTE_SETUP"

echo
echo "Tamanna bootstrap script finished. Checking containers..."
cd /var/www/tamanna
sudo docker compose --profile ai ps
REMOTE

echo
echo "Remote bootstrap command completed. This does not prove public DNS/HTTPS or guest chat works."
echo "Next verify: https://www.bd-king-r7.com/health and POST /api/chat after DNS/TLS are configured."
