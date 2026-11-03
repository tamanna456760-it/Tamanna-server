"""Validate the planned domain configuration; this does not query live DNS."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "domains" / "domain_config.json"
DNS_RECORDS = ROOT / "domains" / "cloudflare-dns-records.json"
DOMAIN = "bd-king-r7.com"
WWW = f"www.{DOMAIN}"


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main():
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    primary = data["domains"]["primary"]
    require(primary.get("domain") == DOMAIN, "Primary domain mismatch")
    require(primary.get("www") == WWW, "Canonical www host mismatch")
    require(primary.get("canonical_url") == f"https://{WWW}/", "Canonical URL mismatch")
    require("legacy_aliases" not in data["domains"], "Unexpected legacy alias configuration")
    require(data["domains"].get("onion", {}).get("enabled") is False,
            "Tor must remain disabled until a real v3 address is configured")

    dns = data["dns"]
    require(dns.get("provider") == "cloudflare", "DNS provider mismatch")
    require(dns.get("nameservers") == ["pablo.ns.cloudflare.com", "uma.ns.cloudflare.com"],
            "Cloudflare nameservers mismatch")

    records = json.loads(DNS_RECORDS.read_text(encoding="utf-8"))
    require(records.get("zone") == DOMAIN, "DNS zone mismatch")
    items = records.get("records", [])
    root = next((r for r in items if r.get("name") == "@"), {})
    www = next((r for r in items if r.get("name") == "www"), {})
    require(root.get("type") == "A", "Apex record must be A")
    require(root.get("content") == "REPLACE_WITH_REAL_ORIGIN_IPV4",
            "Do not commit an unverified/fabricated origin IP")
    require(www.get("type") == "CNAME" and www.get("content") == DOMAIN,
            "www must CNAME to apex")

    nginx = (ROOT / "deploy/nginx/tamanna-domains.conf").read_text(encoding="utf-8")
    require("server_name bd-king-r7.com;" in nginx, "Apex HTTPS vhost missing")
    require("server_name www.bd-king-r7.com;" in nginx, "Canonical www vhost missing")
    require(nginx.count("server_name www.bd-king-r7.com;") == 1,
            "Duplicate www HTTPS server blocks detected")
    require("return 301 https://www.bd-king-r7.com$request_uri;" in nginx,
            "Canonical redirect missing")
    require(nginx.count("/etc/letsencrypt/live/bd-king-r7.com/fullchain.pem") == 2,
            "Both HTTPS vhosts must use the same SAN certificate")

    security = data.get("security", {})
    require(security.get("https_required") is True, "HTTPS must be required")
    require(security.get("expose_private_keys") is False, "Private keys must not be exposed")

    print("PASS: bd-king-r7.com is the only configured primary domain")
    print("PASS: www.bd-king-r7.com is the canonical website host")
    print("PASS: apex redirects to canonical www")
    print("PASS: DNS plan contains no fabricated origin IP")
    print("PASS: Nginx has one SAN certificate and no duplicate www vhost")
    print("NOTE: Live registration, DNS, TLS and hosting are not verified")


if __name__ == "__main__":
    main()
