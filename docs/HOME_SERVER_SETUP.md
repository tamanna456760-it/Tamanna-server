# Tamanna Home Linux Server — ready-to-run guide

This setup is designed for a real Debian/Ubuntu Linux computer on your home LAN.
It does not buy/register a domain, does not use Cloudflare, does not publish a public
DNS zone, and does not modify the router or firewall. The private name is
`tamanna.home.arpa`, reserved for home-network use.

## Important network distinction

The earlier iSH device values (`10.80.38.191` and outbound-visible
`151.247.101.33`) are **not** the home Linux server's LAN address. Do not put
either value into the home DNS zone unless the Linux host itself reports it as
its LAN address and the address is reserved in the router. A public IP observed
by an IP-check service does not prove inbound reachability or static allocation.

## 1. Download the code on the actual Linux host

Open a terminal on the separate Linux computer:

```bash
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/tamanna456760-it/Tamanna-server.git
cd Tamanna-server
git switch infra/home-network-bootstrap
```

If you already cloned it, use:

```bash
cd ~/Tamanna-server
git fetch origin
git switch infra/home-network-bootstrap
git pull --ff-only origin infra/home-network-bootstrap
```

## 2. Read-only inventory (first test)

```bash
bash scripts/home_server_preflight.sh | tee ~/tamanna-home-preflight.txt
```

This only reads OS, CPU, RAM, disks, network addresses, routes, resolver, listening
ports, firewall status, Docker availability and repository status. It does not install
packages or change configuration. Review the output and identify the actual server's
private LAN IPv4 and subnet (for example, server `192.168.1.20`, subnet
`192.168.1.0/24`).

Before enabling DNS, reserve that LAN IP for the Linux host in the router's DHCP
reservation page. Do not guess the subnet or use the iPhone/iSH IP.

## 3. Preview private DNS setup (no changes)

Replace the sample values with the verified Linux host address and LAN subnet:

```bash
TAMANNA_LAN_IP=192.168.1.20 TAMANNA_LAN_CIDR=192.168.1.0/24 \
  sudo --preserve-env=TAMANNA_LAN_IP,TAMANNA_LAN_CIDR \
  bash scripts/install_home_dns.sh
```

The command above is a dry run. It prints the plan and exits without installing or
changing anything.

## 4. Apply only after reviewing the dry-run

```bash
TAMANNA_LAN_IP=192.168.1.20 TAMANNA_LAN_CIDR=192.168.1.0/24 \
  sudo --preserve-env=TAMANNA_LAN_IP,TAMANNA_LAN_CIDR \
  bash scripts/install_home_dns.sh --apply
```

The installer supports Debian/Ubuntu only, validates that the server address is a
private IPv4 inside the supplied subnet, installs BIND, backs up existing BIND
configuration under `/root/tamanna-bind-backup-<timestamp>`, configures the
`home.arpa` zone, validates it with `named-checkconf` and `named-checkzone`,
then enables/restarts `bind9`. It does not change router DHCP, firewall rules,
port forwarding, existing Tamanna application files, or production services.

If BIND already serves DNS on this host, stop and review its existing configuration
before applying; do not overwrite a service you rely on.

## 5. Test from another device on the same LAN

Install DNS tools if needed (`sudo apt-get install -y dnsutils`), then run:

```bash
dig @192.168.1.20 tamanna.home.arpa +short
dig @192.168.1.20 ns1.home.arpa +short
```

Both should return the verified Linux server LAN IP. First test by querying the DNS
server explicitly with `dig @...`. Only after that succeeds should you manually set
one test client's DNS server to the Linux host IP. Keep the router's DHCP DNS setting
unchanged until the single-client test succeeds.

## 6. Rollback

Use the backup path printed by the installer. Restore the backed-up
`named.conf.options` and `named.conf.local`, then inspect and remove only the
Tamanna-created `/etc/bind/db.home.arpa` if appropriate. Run
`named-checkconf` before restarting `bind9`. If the host previously had no BIND
service, disable it with `sudo systemctl disable --now bind9`. Do not delete other
DNS files or change router settings as part of rollback.

## Public Internet is a separate later phase

A private `home.arpa` name resolves only on clients configured to use this home DNS.
It is not a globally delegated Internet domain. Public access later requires a
reachable host, ISP/router inbound policy (or a secure tunnel/relay), TLS, and a
globally delegated registered domain or an approved provider subdomain. Do not expose
this recursive resolver to the Internet and never forward public port 53 to it.

## What is not yet done

Committing these scripts does not install BIND, run Tamanna AI, configure storage
mounts/backups, open firewall ports, or prove public reachability. Those steps require
the real Linux host's preflight output and explicit review. Keep secrets in local
environment files; never commit credentials or private keys.
