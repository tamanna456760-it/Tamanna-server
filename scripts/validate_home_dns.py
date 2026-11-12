"""Static safety checks for the private home.arpa BIND templates."""
from pathlib import Path
import ipaddress

ROOT = Path(__file__).resolve().parents[1]
OPTIONS = ROOT / "deploy/home-dns/named.conf.options.example"
LOCAL = ROOT / "deploy/home-dns/named.conf.local.example"
ZONE = ROOT / "deploy/home-dns/db.home.arpa.example"


def main():
    options = OPTIONS.read_text(encoding="utf-8")
    local = LOCAL.read_text(encoding="utf-8")
    zone = ZONE.read_text(encoding="utf-8")

    assert 'zone "home.arpa"' in local
    assert "allow-update { none; };" in local
    assert "listen-on port 53" in options
    assert "listen-on-v6 { ::1; };" in options
    assert 'allow-query { tamanna_home_clients; };' in options
    assert 'allow-recursion { tamanna_home_clients; };' in options
    assert 'allow-query-cache { tamanna_home_clients; };' in options
    assert "192.168.0.0/16" in options
    assert "10.0.0.0/8" in options
    assert "172.16.0.0/12" in options
    assert "0.0.0.0/0" not in options
    assert "any;" not in options
    assert ".local" not in (options + local + zone)
    assert "bd-king-r7.com" not in (options + local + zone)

    addresses = []
    for line in zone.splitlines():
        stripped = line.strip()
        parts = stripped.split()
        if len(parts) >= 4 and parts[0] in {"ns1", "tamanna"} and parts[1:3] == ["IN", "A"]:
            addresses.append(ipaddress.ip_address(parts[3]))
    assert len(addresses) == 2, "Expected the two example private A records"
    assert all(address.is_private for address in addresses)
    assert all(address == addresses[0] for address in addresses)
    print("PASS: private home.arpa zone is present")
    print("PASS: DNS queries and recursion are limited to private clients")
    print("PASS: no wildcard/public open-recursion ACL is configured")
    print("PASS: example A records use one RFC1918 private address")
    print("NOTE: templates are not installed or running; replace example LAN IP first")


if __name__ == "__main__":
    main()
