# Tamanna AI domain and Cloudflare DNS plan

Primary domain: `bd-king-r7.com`
Canonical website: `https://www.bd-king-r7.com`
Owner attribution: HM INSAN ALI

## Current status

- Cloudflare zone: Pending nameserver verification.
- Assigned nameservers (from the Cloudflare dashboard): `pablo.ns.cloudflare.com` and `uma.ns.cloudflare.com`.
- Domain registration: Not verified by this repository.
- Origin server IPv4: Not supplied; do not invent one.
- Live DNS records: Not created by this repository.

## Intended Cloudflare DNS records

See [cloudflare-dns-records.json](cloudflare-dns-records.json).

1. Register the domain with an accredited registrar.
2. At the registrar, set exactly the two Cloudflare nameservers shown above and remove old nameservers.
3. Wait until Cloudflare Overview reports the zone as Active.
4. Obtain the real public IPv4 of the web origin.
5. In Cloudflare DNS, create an A record for `@` pointing to that IPv4, proxied.
6. Create a CNAME record for `www` pointing to `bd-king-r7.com`, proxied.
7. Configure the origin web server and HTTPS certificate before enabling production traffic.

Do not create an A record using `REPLACE_WITH_REAL_ORIGIN_IPV4`. It is a documentation placeholder, not an IP address.

## Security and email

- Keep origin services behind Cloudflare and restrict the origin firewall to Cloudflare IP ranges only after confirming a working Cloudflare route and an emergency admin path.
- Use Full (strict) TLS after a valid origin certificate is installed.
- MX, SPF, DKIM, and DMARC are intentionally omitted until a real mail provider is selected.
- API, admin, and app subdomains are planned only; do not publish them until their Nginx routing and access controls exist.
- Never commit `.env`, API keys, TLS private keys, or Tor private keys.
