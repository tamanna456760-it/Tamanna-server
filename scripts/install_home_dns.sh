#!/usr/bin/env bash
# Explicit opt-in BIND setup for a private home.arpa zone on Debian/Ubuntu.
set -Eeuo pipefail
APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1
: "${TAMANNA_LAN_IP:=}"
: "${TAMANNA_LAN_CIDR:=}"
: "${TAMANNA_ZONE:=home.arpa}"
if [[ -z "$TAMANNA_LAN_IP" || -z "$TAMANNA_LAN_CIDR" ]]; then
  echo "Set TAMANNA_LAN_IP and TAMANNA_LAN_CIDR first." >&2
  echo "Example: TAMANNA_LAN_IP=192.168.1.10 TAMANNA_LAN_CIDR=192.168.1.0/24" >&2
  exit 2
fi
python3 - "$TAMANNA_LAN_IP" "$TAMANNA_LAN_CIDR" <<'PY'
import ipaddress, sys
ip = ipaddress.ip_address(sys.argv[1])
net = ipaddress.ip_network(sys.argv[2], strict=False)
if ip.version != 4 or not ip.is_private or ip not in net:
    raise SystemExit("LAN IP must be a private IPv4 address inside the supplied LAN CIDR")
if net.prefixlen < 16 or net.prefixlen > 30:
    raise SystemExit("Use a realistic LAN CIDR between /16 and /30")
PY
if [[ "$TAMANNA_ZONE" != "home.arpa" ]]; then
  echo "Only the reserved private-use home.arpa zone is supported." >&2
  exit 2
fi
if [[ ! -r /etc/os-release ]]; then echo "Cannot identify OS; aborting."; exit 2; fi
. /etc/os-release
case "${ID:-}" in debian|ubuntu) ;; *) echo "Supported OS: Debian/Ubuntu only (found ${ID:-unknown})."; exit 2;; esac
if [[ $EUID -ne 0 ]]; then echo "Run with sudo: sudo -E $0 --apply"; exit 2; fi
if [[ $APPLY -ne 1 ]]; then
  cat <<EOF
DRY RUN — no changes made.
Would install bind9 and bind9-utils.
Would configure authoritative/recursive DNS for $TAMANNA_ZONE.
Server LAN IP: $TAMANNA_LAN_IP
Allowed client subnet: $TAMANNA_LAN_CIDR
Would validate configuration, then enable/restart bind9.
Review router DHCP DNS settings manually; this script will NOT change your router/firewall.
To apply after reserving this server IP in your router:
  sudo env TAMANNA_LAN_IP='$TAMANNA_LAN_IP' TAMANNA_LAN_CIDR='$TAMANNA_LAN_CIDR' $0 --apply
EOF
  exit 0
fi
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y bind9 bind9-utils
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="/root/tamanna-bind-backup-$STAMP"
mkdir -m 700 "$BACKUP"
cp -a /etc/bind/named.conf.options "$BACKUP/" 2>/dev/null || true
cp -a /etc/bind/named.conf.local "$BACKUP/" 2>/dev/null || true
cat > /etc/bind/named.conf.options <<EOF
acl "tamanna_home_clients" {
    127.0.0.1;
    $TAMANNA_LAN_CIDR;
};
options {
    directory "/var/cache/bind";
    listen-on port 53 { 127.0.0.1; $TAMANNA_LAN_IP; };
    listen-on-v6 { none; };
    recursion yes;
    allow-query { tamanna_home_clients; };
    allow-recursion { tamanna_home_clients; };
    allow-query-cache { tamanna_home_clients; };
    dnssec-validation auto;
};
EOF
cat > /etc/bind/named.conf.local <<'EOF'
zone "home.arpa" {
    type primary;
    file "/etc/bind/db.home.arpa";
    allow-update { none; };
};
EOF
cat > /etc/bind/db.home.arpa <<EOF
$TTL 300
@ IN SOA ns1.home.arpa. hostmaster.home.arpa. (
  2026111201 3600 900 1209600 300
)
  IN NS ns1.home.arpa.
ns1 IN A $TAMANNA_LAN_IP
tamanna IN A $TAMANNA_LAN_IP
EOF
chown root:bind /etc/bind/db.home.arpa 2>/dev/null || true
chmod 640 /etc/bind/db.home.arpa
named-checkconf
named-checkzone home.arpa /etc/bind/db.home.arpa
if systemctl enable bind9 && systemctl restart bind9; then
  echo "BIND started. Backup: $BACKUP"
  echo "Test from a LAN client: dig @$TAMANNA_LAN_IP tamanna.home.arpa"
  echo "Do NOT expose/forward port 53 to the public Internet."
else
  echo "BIND failed. Previous configs are backed up at $BACKUP; inspect systemctl status bind9." >&2
  exit 1
fi
