# Tamanna AI domain and Cloudflare DNS plan

Primary domain: `bd-king-r7.com`
Canonical website: `https://www.bd-king-r7.com`
Legacy redirect alias to retain: `https://www.tamanna.com`
Owner attribution: HM INSAN ALI

## Current status

- Cloudflare zone for `bd-king-r7.com`: Pending nameserver verification.
- Assigned nameservers (from the Cloudflare dashboard): `pablo.ns.cloudflare.com` and `uma.ns.cloudflare.com`.
- Domain registration: Not verified by this repository.
- Origin server IPv4: Not supplied; do not invent one.
- Live DNS records: Not created by this repository.
- `www.tamanna.com` must remain resolvable and have a valid TLS certificate so it can redirect to the new canonical host.

## Intended DNS records

For `bd-king-r7.com`, see [cloudflare-dns-records.json](cloudflare-dns-records.json).

The separate `tamanna.com` DNS zone must also retain a `www` record pointing to the same web origin. Configure that record at the DNS provider authoritative for `tamanna.com`; do not change its nameservers as part of this migration unless separately planned and verified.

## Migration steps

1. Confirm that `bd-king-r7.com` is registered with an accredited registrar.
2. At that domain's registrar, set exactly the Cloudflare nameservers shown above and wait for the zone to become Active.
3. Obtain the real public IPv4 of the web origin.
4. In the new Cloudflare zone, create an A record for `@` and a CNAME for `www`.
5. In the existing `tamanna.com` DNS zone, keep `www.tamanna.com` pointed at the same origin.
6. Issue valid certificates for both new canonical hosts and the old `www.tamanna.com` alias.
7. Configure Nginx to redirect the old alias to `https://www.bd-king-r7.com`.

Do not create an A record using `REPLACE_WITH_REAL_ORIGIN_IPV4`. It is a documentation placeholder, not an IP address.

## Security and email

- Keep origin services behind Cloudflare and restrict the origin firewall to Cloudflare IP ranges only after confirming a working Cloudflare route and an emergency admin path.
- Use Full (strict) TLS after valid origin certificates are installed.
- MX, SPF, DKIM, and DMARC are intentionally omitted until a real mail provider is selected.
- API, admin, and app subdomains are planned only; do not publish them until their Nginx routing and access controls exist.
- Never commit `.env`, API keys, TLS private keys, or Tor private keys.
