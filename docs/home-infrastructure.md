# Tamanna Home Infrastructure (private-first)

This plan deliberately does **not** register or assume ownership of a public domain.
It starts with a private home network and preserves the existing public-domain deployment
configuration for a future, separately approved migration.

## Naming and scope

- Use \`home.arpa\` for private home-network names (for example, \`tamanna.home.arpa\`).
- Do not use \`.local\`; it is reserved for Multicast DNS.
- \`home.arpa\` is not a globally delegated public domain. It will resolve only for clients
  configured to use the home DNS resolver (or a router that forwards to it).
- A future globally reachable service still needs routable public connectivity and a
  globally delegated name, or another supported public addressing/discovery mechanism.
  Running a private authoritative DNS server alone cannot make a new TLD globally resolvable.

## Phase 1 — read-only host inventory

Before installing anything, record:
- Linux distribution/version and kernel
- CPU, RAM and storage capacity/health
- LAN interface, private IPv4 address, gateway and DHCP arrangement
- Existing DNS resolver and whether the router supports DHCP DNS options
- Listening ports, firewall policy and whether Docker/Podman is installed
- Current Tamanna repository branch, commit and working-tree status

Do not print \`.env\`, tokens, private keys, or database contents. Do not change firewall,
router, DHCP, DNS, or service state during inventory.

## Phase 2 — private DNS design

The BIND examples in \`deploy/home-dns/\` are templates only. Before enabling them:
1. Choose a stable LAN address for the Linux server (prefer a DHCP reservation on the router).
2. Replace the example address in the zone file with that actual LAN address.
3. Confirm TCP and UDP port 53 are available and that the resolver will listen only on
   loopback and the trusted LAN.
4. Configure recursion/query access for localhost and private LAN clients only.
5. Test the zone with \`named-checkconf\` and \`named-checkzone\`.
6. Configure one test client to use the home DNS server; verify
   \`tamanna.home.arpa\` resolves to the server's LAN address.
7. Keep the router's existing DNS settings unchanged until the test client succeeds.

Never expose this private resolver as an open recursive resolver on the public Internet.
Do not forward port 53 from the router to this host.

## Phase 3 — application and storage

- Keep the existing Flask API and Tamanna AI app separate.
- Keep API ports bound to loopback or a trusted private interface; expose only a reviewed
  reverse proxy if remote access is later approved.
- Use explicit persistent data directories and tested backups.
- Keep secrets in a root-readable local \`.env\`; never commit real values.
- Start with the existing SQLite setup for a single-node test. Evaluate a managed local
  database only after measuring workload and backup/restore requirements.

## Rollback

The private DNS service is additive. To roll it back, stop/disable only the new BIND
service and restore the test client's previous DNS setting. Do not remove or rewrite
existing \`Dns/\`, Cloudflare, Nginx, or production deployment files as part of this phase.

## Not yet verified

No home-server hardware, LAN address, router configuration, inbound public connectivity,
or live DNS service has been inspected from GitHub. A committed template is not a running
server. Do not claim public availability until external-network tests pass.
