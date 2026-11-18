# Tamanna Server Admin Panel

The server admin UI is served by the Flask application at `/admin/`.

## Scope
- Read-only liveness check: `GET /health`.
- Read-only database readiness check: `GET /health/ready`.
- Links to the separate Tamanna AI Admin panel and source repositories.

## Security boundary
This first version deliberately does not expose privileged operations, environment variables, database rows, server logs, shell commands, deployment actions, or personal profile data. The two health endpoints are intentionally public and return minimal status only. CPU/RAM/disk telemetry and operational controls require a separately authenticated admin API, session/role checks, audit logging, and tests before being enabled.

## Files
- `admin/index.html`
- `admin/assets/admin.css`
- `admin/assets/admin.js`

## URLs
- Server admin: `/admin/`
- Tamanna AI admin: `https://tamanna456760-it.github.io/tamanna-website/admin/`
