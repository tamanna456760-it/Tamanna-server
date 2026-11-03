# TAMANNA CENTRAL SERVER

Core infrastructure for Tamanna AI.

- Owner: HM INSAN ALI
- Repository: tamanna456760-it/Tamanna-server
- Primary planned domain: `bd-king-r7.com`
- Canonical website: `https://www.bd-king-r7.com`
- Status: Under development and security audit

## Domain and DNS

The intended public hosts are `bd-king-r7.com` and `www.bd-king-r7.com`. Cloudflare zone verification is currently pending, and domain registration has not been independently verified by this repository. The Cloudflare nameservers supplied by the dashboard are `pablo.ns.cloudflare.com` and `uma.ns.cloudflare.com`.

See [domains/README.md](domains/README.md) and [domains/cloudflare-dns-records.json](domains/cloudflare-dns-records.json). A real origin IPv4 and an active Cloudflare zone are required before publishing DNS. No placeholder IP is a usable DNS target.

## Install

```sh
git clone https://github.com/tamanna456760-it/Tamanna-server.git
cd Tamanna-server
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

Set a unique `ORCHESTRATOR_TOKEN` in the local `.env`; never commit secrets.

## Validate

```sh
python scripts/validate_json.py
python scripts/validate_domains.py
python -m compileall -q app.py server.py agent.py apps.py synce.py tests scripts
python -m pytest -q
```

Deployment instructions: [deploy/README.md](deploy/README.md).

A successful CI workflow does not prove that the live DNS, Cloudflare zone, TLS certificate, origin server, or production website is operational. Production deployment remains manual and requires approval.
