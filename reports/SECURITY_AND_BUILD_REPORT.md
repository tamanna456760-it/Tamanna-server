# Tamanna Central Server — Security and Build Report

Date: 2026-11-03
Branch: main
Scope: Central Server only. This report does not certify the separate Tamanna AI repository.

## Changes recorded in GitHub

- Added HMAC-SHA256 service protocol v1 for signed service reports.
- Added timestamp, key ID, nonce, exact request-body digest, signature verification, and constant-time comparison.
- Added Redis-backed atomic nonce claims (SET NX with expiry) for replay protection across workers/hosts.
- Added an internal Redis 7.4 service to Docker Compose; Redis has no published host port.
- Configured fail-closed behavior when Redis is configured but unavailable.
- Kept process-local nonce fallback for local development only; do not use it for multi-worker or multi-host production.
- Added tests for valid signatures, invalid/tampered requests, replay, Redis atomic claims, Redis outage fail-closed behavior, public metadata, and unsigned report rejection.
- Updated protocol and environment documentation.

## Verification status

- GitHub file updates: committed to main.
- Python tests: PENDING GitHub Actions result.
- Docker Compose validation/build: PENDING GitHub Actions result.
- .NET build job: PENDING GitHub Actions result; do not assume it passed.
- Live server deployment and HTTPS: NOT VERIFIED.

## Production prerequisites

1. Set a strong TAMANNA_SERVICE_SHARED_SECRET in the server's private .env; never commit it.
2. Configure the AI client with the same secret under its own environment variable.
3. Keep Redis private to the Compose network and monitor its health.
4. Use HTTPS through a trusted reverse proxy for public traffic.
5. Configure distributed edge rate limiting/WAF and NTP clock synchronization.
6. Review Redis availability, backups, and operational monitoring before production.

## Important boundary

This protocol authorizes signed service reports only. It does not grant shell access, arbitrary code execution, deployment, account administration, or unrestricted database access.
