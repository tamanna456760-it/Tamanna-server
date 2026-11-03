import json
import re
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "domains" / "domain_config.json"
DOMAIN_RE = re.compile(r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


def main():
    if not CONFIG.is_file():
        raise SystemExit(f"FAIL: configuration not found: {CONFIG}")

    try:
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"FAIL: invalid JSON at line {exc.lineno}: {exc.msg}")

    domains = data.get("domains", {})
    for key in ("primary", "secondary", "onion"):
        if key not in domains:
            raise SystemExit(f"FAIL: missing domains.{key}")

    for key in ("primary", "secondary"):
        item = domains[key]
        for field in ("domain", "www"):
            hostname = item.get(field, "").lower()
            if not DOMAIN_RE.fullmatch(hostname):
                raise SystemExit(f"FAIL: invalid {key}.{field}: {hostname!r}")

    if domains["secondary"].get("redirect_target") != "https://www.tamanna.com":
        raise SystemExit("FAIL: unexpected secondary redirect target")

    if domains["onion"].get("enabled") is True:
        raise SystemExit("FAIL: onion service must remain disabled until separately deployed")

    api_host = data.get("subdomains", {}).get("api", {}).get("hostname")
    if api_host != "api.tamanna.com":
        raise SystemExit("FAIL: unexpected API hostname")

    print("PASS: domain configuration structure and safety checks passed")
    print("Primary:", domains["primary"]["domain"])
    print("Secondary:", domains["secondary"]["domain"])
    print("API:", api_host)
    print("Tor hidden service: disabled (safe default)")


if __name__ == "__main__":
    main()
