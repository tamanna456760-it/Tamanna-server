# Tamanna Server Deployment

This repository currently deploys the **report orchestrator** in `app.py`.
It is not yet the complete Tamanna AI chat, voice, memory, identity, or agent platform.
Do not describe those modules as deployed until they exist and pass tests.

## Local Linux / VPS prerequisites

- Ubuntu 22.04+ or another supported Linux distribution
- Docker Engine with the Docker Compose v2 plugin
- Git, Python 3.12+, and curl
- A server account allowed to run Docker
- DNS control and a public IP are needed only for public-domain deployment

## Configure and start

From the repository root:

```bash
cp .env.example .env
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Paste the generated value into `.env` as `ORCHESTRATOR_TOKEN=...`.
Never commit `.env`, API keys, TLS keys, or Tor keys.

Then run:

```bash
chmod +x scripts/*.sh
./scripts/start_server.sh
```

The container binds to `127.0.0.1:8000`, not the public interface.
Check status and logs:

```bash
docker compose ps
docker compose logs --tail=100 orchestrator
curl --fail http://127.0.0.1:8000/health
```

Stop without deleting database data:

```bash
./scripts/stop_server.sh
```

## Public DNS and HTTPS

Only configure Nginx after the domain registrant points these names to the server:
- `www.tamanna.com`, `tamanna.com`
- `tamanna.io`, `www.tamanna.io`
- `api.tamanna.com`

Obtain a certificate that covers every hostname before enabling
`deploy/nginx/tamanna-domains.conf`. The production Nginx file references
`/etc/letsencrypt/live/tamanna.com/fullchain.pem` and `privkey.pem`;
those files must exist first. Use the HTTP bootstrap file for ACME validation,
then issue the certificate and switch to the production file. Do not expose
port 8000 directly to the internet.

## Not included / external prerequisites

- No hosting provider, VPS, SSH credentials, public IP, or DNS-zone access is
  supplied by this repository. The scripts cannot create a paid domain or VPS.
- Tor v3 creates its own address; the requested literal `Tamanna.onion`
  cannot be selected as the address. Keep Tor disabled until separately tested.
- The current Flask app is a report dashboard/API, not the full AI platform.
- Database backup, restore drills, production monitoring, WAF, and domain
  ownership verification still require environment-specific setup.
