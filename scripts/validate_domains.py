"""Validate the planned domain configuration; this does not query live DNS."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "domains" / "domain_config.json"
DNS_RECORDS = ROOT / "domains" / "cloudflare-dns-records.json"
OLD_DOMAIN = "tamanna.com"
NEW_DOMAIN = "bd-king-r7.com"


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main():
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    domains = data.get("domains", {})
    primary = domains.get("primary", {})
    onion = domains.get("onion", {})
    require(primary.get("domain") == NEW_DOMAIN, "Primary domain must be bd-king-r7.com")
    require(primary.get("www") == f"www.{NEW_DOMAIN}", "WWW host is incorrect")
    require(primary.get("registration_status") == "unverified", "Do not claim registration without verification")
    require(primary.get("cloudflare_zone_status") == "pending", "Cloudflare pending state must be explicit")
    require(onion.get("enabled") is False, "Tor must remain disabled until a real v3 address is configured")

    subdomains = data.get("subdomains", {})
    for name in ("api", "admin", "app"):
        require(subdomains.get(name) == f"{name}.{NEW_DOMAIN}", f"{name} hostname is incorrect")

    dns = data.get("dns", {})
    require(dns.get("provider") == "cloudflare", "DNS provider must be Cloudflare")
    require(dns.get("nameservers") == ["pablo.ns.cloudflare.com", "uma.ns.cloudflare.com"],
            "Cloudflare nameservers do not match the supplied dashboard values")

    records = json.loads(DNS_RECORDS.read_text(encoding="utf-8"))
    require(records.get("zone") == NEW_DOMAIN, "DNS records zone mismatch")
    require(records.get("records", [{}])[0].get("content") == "REPLACE_WITH_REAL_ORIGIN_IPV4",
            "Do not publish a fabricated origin IP")
    require(records.get("records", [{}])[0].get("type") == "A", "Root DNS record must be an A record")

    legacy_domain = "tamanna" + ".com"
    active_files = [
        ROOT / "README.md",
        ROOT / ".env.example",
        ROOT / "Metadata.json",
        ROOT / "Config" / "Config.json",
        ROOT / "deploy" / "README.md",
        ROOT / "deploy" / "nginx" / "acme-bootstrap.conf",
        ROOT / "deploy" / "nginx" / "tamanna-domains.conf",
        ROOT / "tests" / "test_server_health.py",
    ]
    for path in active_files:
        require(legacy_domain not in path.read_text(encoding="utf-8"),
                f"Legacy primary domain remains in {path.relative_to(ROOT)}")

    security = data.get("security", {})
    require(security.get("https_required") is True, "HTTPS must be required")
    require(security.get("tls_minimum") in {"1.2", "1.3"}, "TLS minimum must be 1.2 or 1.3")
    require(security.get("expose_private_keys") is False, "Private keys must never be exposed")

    print("PASS: bd-king-r7.com domain plan is structurally valid")
    print("PASS: Cloudflare nameservers match the supplied dashboard")
    print("PASS: DNS origin IP is an explicit placeholder, not a fabricated address")
    print("NOTE: Domain registration, nameserver propagation, live DNS, TLS, and hosting are NOT verified")


if __name__ == "__main__":
    main()
