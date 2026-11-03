# Tamanna AI domain and Cloudflare DNS plan

Primary domain: `bd-king-r7.com`
Canonical website: `https://www.bd-king-r7.com`
Apex redirect: `https://bd-king-r7.com/*` → `https://www.bd-king-r7.com/*`
Owner attribution: HM INSAN ALI

## Current status

- Cloudflare nameservers supplied: `pablo.ns.cloudflare.com` and `uma.ns.cloudflare.com`.
- Domain registration: unverified.
- Cloudflare zone activation: pending verification.
- Origin server IPv4: not supplied; do not invent one.
- Live DNS records: not created by this repository.

## DNS records

See [cloudflare-dns-records.json](cloudflare-dns-records.json). Replace the A-record placeholder only after confirming the real public IPv4 of the production VPS. The `www` CNAME targets the apex domain. Do not publish placeholder values.

## Setup

1. Verify domain registration and Cloudflare zone ownership.
2. Set the assigned Cloudflare nameservers at the registrar, then wait for the zone to become Active.
3. Obtain the actual public IPv4 of the production VPS.
4. Create the apex A record and `www` CNAME in Cloudflare.
5. Issue one certificate containing both `bd-king-r7.com` and `www.bd-king-r7.com`.
6. Install and validate the Nginx configuration.
7. Verify HTTP-to-HTTPS and apex-to-www redirects from an external network.

## DNSSEC

The DS record must match the current DS value shown by Cloudflare exactly. Do not copy an old DS record blindly; a mismatch can make the domain fail to resolve.

## Security

- Use Cloudflare Full (strict) after origin TLS is installed.
- Do not expose API/admin/app subdomains until routing and access controls exist.
- MX, SPF, DKIM and DMARC remain unconfigured until a mail provider is selected.
- Never commit `.env`, API keys, TLS private keys or Tor private keys.
