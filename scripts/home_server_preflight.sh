#!/usr/bin/env bash
# Read-only inventory for a Debian/Ubuntu home Linux host.
set -u
section(){ printf '\n========== %s ==========\n' "$1"; }
section "OS"
cat /etc/os-release 2>/dev/null || true
uname -a
section "CPU AND MEMORY"
nproc 2>/dev/null || true
free -h 2>/dev/null || cat /proc/meminfo 2>/dev/null | head -8
section "STORAGE"
df -hT
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT 2>/dev/null || true
section "NETWORK"
ip -brief address 2>/dev/null || true
ip route 2>/dev/null || true
section "DNS RESOLVER"
cat /etc/resolv.conf 2>/dev/null || true
section "LISTENING PORTS"
if command -v ss >/dev/null 2>&1; then ss -lntup; else echo "ss not installed"; fi
section "FIREWALL (READ ONLY)"
if command -v ufw >/dev/null 2>&1; then ufw status; fi
if command -v nft >/dev/null 2>&1; then sudo -n nft list ruleset 2>/dev/null || echo "nft rules unavailable without sudo"; fi
section "CONTAINER RUNTIME"
docker --version 2>/dev/null || echo "Docker not installed"
docker compose version 2>/dev/null || true
section "TAMANNA CHECKOUT"
for d in "$HOME/Tamanna-server" "$HOME/Tamanna-"; do
  if [ -d "$d/.git" ]; then
    echo "Repository: $d"
    git -C "$d" status --short --branch
    git -C "$d" log -1 --oneline
  fi
done
section "PREFLIGHT COMPLETE"
echo "Read-only only: no packages, services, firewall, DNS, or files were changed."
