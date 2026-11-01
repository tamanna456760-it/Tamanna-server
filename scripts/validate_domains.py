
import json
from pathlib import Path

CONFIG = Path(__file__).resolve().parents[1] / "domains" / "domain_config.json"

def main():
    if not CONFIG.exists():
        raise SystemExit("FAIL: Domain configuration not found")

    with CONFIG.open("r", encoding="utf-8") as file:
        data = json.load(file)

    domains = data.get("domains", {})
    required = ["primary", "secondary", "onion"]

    for name in required:
        if name not in domains:
            raise SystemExit(f"FAIL: Missing domain configuration: {name}")

    print("PASS: Tamanna domain configuration is valid")
    print("Primary:", domains["primary"]["domain"])
    print("Secondary:", domains["secondary"]["domain"])
    print("Onion setup enabled:", domains["onion"]["enabled"])

if __name__ == "__main__":
    main()
