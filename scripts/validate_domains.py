"""Validate the checked-in Tamanna domain plan without claiming live DNS status."""
import json
from pathlib import Path
from urllib.parse import urlparse

CONFIG = Path(__file__).resolve().parents[1] / "domains" / "domain_config.json"


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main():
    require(CONFIG.is_file(), "Domain configuration not found")
    try:
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"FAIL: Cannot read domain configuration: {exc}") from exc

    domains = data.get("domains")
    require(isinstance(domains, dict), "domains must be an object")
    primary = domains.get("primary", {})
    secondary = domains.get("secondary", {})
    onion = domains.get("onion", {})

    require(primary.get("domain") == "tamanna.com", "Primary domain must be tamanna.com")
    require(primary.get("www") == "www.tamanna.com", "Primary www host must be www.tamanna.com")
    require(secondary.get("domain") == "tamanna.io", "Secondary domain must be tamanna.io")
    require(secondary.get("www") == "www.tamanna.io", "Secondary www host must be www.tamanna.io")
    target = urlparse(secondary.get("redirect_target", ""))
    require(target.scheme == "https" and target.netloc == "www.tamanna.com", "Secondary redirect must use the HTTPS primary website")
    require(onion.get("enabled") is False, "Tor hidden service must remain disabled until an actual v3 address is configured")

    security = data.get("security", {})
    require(security.get("https_required") is True, "HTTPS must be required")
    require(security.get("tls_minimum") in {"1.2", "1.3"}, "TLS minimum must be 1.2 or 1.3")
    require(security.get("expose_private_keys") is False, "Private keys must never be exposed")

    print("PASS: Domain configuration is structurally valid")
    print("NOTE: This check does not verify domain ownership, live DNS, TLS, or hosting.")


if __name__ == "__main__":
    main()
