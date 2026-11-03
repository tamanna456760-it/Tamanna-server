# Tamanna Central Server

Tamanna AI server and website repository.

## Domain plan

| Hostname | Purpose |
|---|---|
| `www.bd-king-r7.com` | Canonical production website |
| `bd-king-r7.com` | Redirect to canonical `www` host |
| `www.tamanna.com` | Retained legacy HTTPS redirect to `www.bd-king-r7.com` |

The new domain's registration, Cloudflare activation, DNS records, origin IPv4, and production hosting must be verified separately. The old `www.tamanna.com` DNS and TLS certificate must remain active for its redirect to work.

See [domains/README.md](domains/README.md) and [deploy/README.md](deploy/README.md) for the DNS and deployment procedure.
