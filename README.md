TAMANNA CENTRAL SERVER

The Core Infrastructure of Tamanna AI

Project: Tamanna Central Server
Owner: HM INSAN ALI
Repository: tamanna456760-it/Tamanna-server
Branch: main
Status: Under Development & Security Audit

⸻

1. Project Overview

Tamanna Central Server is designed to be the central backend infrastructure of the Tamanna AI ecosystem.

Its purpose is to provide a unified, secure, scalable and self-managed platform for managing AI services, APIs, users, devices, databases, automation, networking, monitoring and connected systems.

The central server will act as the primary control point for authorized Tamanna services.

2. Core Mission

* Build an independent, self-hosted server infrastructure.
* Manage all authorized Tamanna services from one central system.
* Provide secure communication between applications and services.
* Manage users, devices, permissions and identities.
* Support AI models and intelligent agents.
* Maintain centralized data and storage.
* Provide monitoring, logging, auditing and recovery.
* Support future multi-server deployment and high availability.

3. System Architecture

              TAMANNA ECOSYSTEM
                      |
          Web / Mobile / Admin Panel
                      |
                 HTTPS / TLS
                      |
             Reverse Proxy / WAF
                      |
             CENTRAL API SERVER
                      |
       +--------------+--------------+
       |              |              |
     CORE          SECURITY        IDENTITY
       |              |              |
       +--------------+--------------+
                      |
             SERVICE ORCHESTRATOR
                      |
       +--------------+--------------+
       |              |              |
      AI           DATABASE        STORAGE
    SERVICES       SERVICES        SERVICES
       |              |              |
       +--------------+--------------+
                      |
              MONITORING & AUDIT
                      |
              BACKUP & RECOVERY

4. Main Server Modules

Module	Responsibility
Core	Main server engine
API	API endpoints and request handling
Security	Authentication and authorization
Identity	Users, devices and service identities
Database	Central data management
AI Engine	AI provider integration
Agents	Authorized AI agents
Orchestration	Service coordination
Network	Trusted network integrations
Storage	File and data storage
Monitoring	Health and performance
Logging	System and audit logs
Backup	Backup and recovery
Cluster	Future multi-server coordination
Deployment	Server deployment management

These are target architectural modules. Their presence and implementation must be verified against the actual repository.

5. Technology Stack

Technology	Purpose
Python	Main backend language
Flask	Existing HTTP application framework
SQLAlchemy	Database integration
SQLite	Development database option
Docker	Containerization
Docker Compose	Service orchestration
Nginx	Reverse proxy
HTTPS / TLS	Secure communication
GitHub	Source code management
AI APIs	Optional AI provider integration

The final production stack must be confirmed against the actual source code and deployment configuration.

6. Repository Structure

Tamanna-server/
│
├── README.md
├── LICENSE
├── requirements.txt
├── app.py
├── server.py
├── main.py
│
├── api/
├── core/
├── security/
├── identity/
├── database/
├── agents/
├── orchestration/
├── network/
├── storage/
├── monitoring/
├── backup/
├── cluster/
│
├── tests/
├── scripts/
├── deploy/
│   ├── nginx/
│   └── tor/
│
├── data/
├── logs/
│
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── .env.example
│
└── .github/
    └── workflows/

This is the target structure, not a claim that every directory currently exists. Preserve existing files and inspect before adding or renaming anything.

7. Domain & Service Configuration

Planned domain endpoints:

Domain	Intended Purpose
www.bd-king-r7.com	Canonical production web access
bd-king-r7.com	Redirect to canonical www host
www.bd-king-r7.com	Retained legacy HTTPS redirect to www.bd-king-r7.com
tamanna.io	Additional domain (not migrated)
Tamanna.onion	Planned Tor hidden service

Domain ownership, DNS records, TLS certificates and actual deployment must be configured and verified separately.

8. Installation

Clone the repository:

git clone https://github.com/tamanna456760-it/Tamanna-server.git
cd Tamanna-server

Create a virtual environment:

python3 -m venv .venv
source .venv/bin/activate

Install dependencies:

python -m pip install --upgrade pip
pip install -r requirements.txt

Create the local environment file:

cp .env.example .env

Configure the required variables in .env.

Never commit .env to GitHub.

9. Environment Configuration

Example configuration:

APP_NAME=Tamanna Central Server
APP_ENV=development
APP_DEBUG=false
HOST=127.0.0.1
PORT=8000
ORCHESTRATOR_TOKEN=
AI_MODE=local
GEMINI_API_KEY=
OPENAI_API_KEY=
DEEP_API_KEY=
DATABASE_URL=sqlite:///./data/tamanna.db
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_PER_MINUTE=60
LOG_LEVEL=INFO
LOG_DIRECTORY=logs
BACKUP_ENABLED=true
BACKUP_DIRECTORY=backups

Only use environment variables that are supported by the application. Production secrets must be strong, unique and stored securely.

10. API Design

Planned API groups:

API	Purpose
/health	Health status
/api/auth	Authentication
/api/users	User management
/api/agents	Agent management
/api/ai	AI services
/api/storage	Storage operations
/api/monitoring	Monitoring
/api/backup	Backup management
/api/admin	Authorized administration

These are proposed endpoints. Implement and document each route before treating it as available.

11. Security Architecture

Security is a fundamental requirement.

* Strong authentication.
* Role-based access control.
* Secure session and token management.
* HTTPS and TLS.
* Input validation.
* Request size limits.
* Rate limiting.
* CORS restrictions.
* Security headers.
* Firewall and network restrictions.
* Audit logging.
* Dependency vulnerability checks.
* Backup encryption.
* Least-privilege service permissions.

No hardcoded production credentials or insecure fallback tokens are permitted.

12. Database & Storage

The central server should support:

* User records.
* Service identities.
* AI configurations.
* Application settings.
* System audit records.
* Authorized automation history.
* File metadata.
* Backup metadata.

Production database selection, migrations, retention and access controls must be configured before deployment.

13. AI & Agent Integration

Planned AI capabilities:

* Gemini integration.
* Other explicitly configured AI providers.
* AI request routing.
* Agent orchestration.
* Knowledge and documentation indexing.
* Context management.
* Controlled tool execution.
* Human approval for sensitive actions.

Agents must operate with limited permissions and must not execute arbitrary commands without authorization.

14. Monitoring & Logging

The monitoring system should track:

* Server availability.
* CPU and memory usage.
* Disk capacity.
* API response status.
* Application errors.
* Database availability.
* Service health.
* Authentication events.
* Administrative actions.

Logs must not contain passwords, API keys, access tokens or other secrets.

15. Backup & Disaster Recovery

Required capabilities:

* Scheduled backups.
* Encrypted backup storage.
* Database backup.
* Configuration backup without exposing secrets.
* Backup integrity verification.
* Restore procedures.
* Recovery testing.
* Retention policies.

A backup is not considered reliable until restoration has been tested.

16. Docker Deployment

Validate the configuration before deployment:

docker compose config

Build the image:

docker compose build

Start services:

docker compose up -d

Inspect service status:

docker compose ps

View logs:

docker compose logs --tail=100

These commands assume the Docker configuration is valid and the required services are defined.

17. Testing & Quality Assurance

Run automated tests:

python -m pytest -q

Before production deployment, verify:

* Application startup.
* API functionality.
* Authentication.
* Authorization.
* Database connectivity.
* Input validation.
* Health checks.
* Backup restoration.
* Container security.
* TLS configuration.
* Recovery procedures.

18. CI/CD & GitHub Integration

The repository should support:

* Automated tests.
* Code quality checks.
* Security scanning.
* Dependency review.
* Build validation.
* Controlled deployment.
* Deployment logs.
* Rollback procedures.

GitHub Actions must use least-privilege permissions. Automatic code changes and production deployments require explicit authorization and review.

19. Development Roadmap

Phase	Goal
Phase 1	Security baseline
Phase 2	Central API and core engine
Phase 3	Identity and access management
Phase 4	Database and storage
Phase 5	AI and agent integration
Phase 6	Monitoring and backup
Phase 7	Docker and production deployment
Phase 8	Multi-server architecture
Phase 9	High availability and disaster recovery

20. Contribution Rules

1. Inspect existing code before modifying it.
2. Never delete working files without approval.
3. Use separate branches for significant changes.
4. Keep secrets outside GitHub.
5. Add tests for new functionality.
6. Review security implications.
7. Document configuration changes.
8. Require approval for production changes.

21. Production Readiness Checklist

* [ ]	Repository structure audited.
* [ ]	All entry points identified.
* [ ]	Secrets rotated and protected.
* [ ]	Authentication verified.
* [ ]	Authorization verified.
* [ ]	Database configured.
* [ ]	API tests passing.
* [ ]	Health checks working.
* [ ]	Docker configuration validated.
* [ ]	Nginx configuration validated.
* [ ]	HTTPS certificates installed.
* [ ]	Firewall configured.
* [ ]	Backup and restore tested.
* [ ]	Monitoring enabled.
* [ ]	CI/CD security reviewed.
* [ ]	Staging deployment verified.
* [ ]	Production deployment approved.

22. License

See the repository’s LICENSE file for applicable licensing terms. Do not assume a license if no license file is present.

⸻

Tamanna Central Server
Owner Attribution: HM INSAN ALI
Repository: https://github.com/tamanna456760-it/Tamanna-server

Building a secure, independent and scalable foundation for the Tamanna AI ecosystem.

---

## 23. Verified runtime entry points and repository audit notes

The repository currently contains multiple historical applications. They are **not one integrated server** and must not all be started together.

| Entry point | Purpose | Current status |
|---|---|---|
| `app.py` / `server.py` | Primary Flask report API on port 8000 | Current Compose service |
| `Wabsite/Index.html` | Public static website | Served by the Nginx configuration |
| `server.js` | Optional Node static-site preview on port 3000 | Syntax and integration tests in CI |
| `program.cs` | Separate .NET report API | Security-hardened; build checked in CI |
| `agent.py` | Optional local Git automation agent | Shell execution removed; requires trusted local YAML config |
| `apps.py` | Legacy analytics application | Not in Compose; requires the missing `bd_king_ai` module and its optional data-science dependencies |
| `synce.py` | Legacy medical/Google integration | Not in Compose; requires missing `google_sync` and `master_doctor_ai` modules and private credentials |
| `main.py` | Old sample worker | Not the web-server entry point |

Do not deploy `apps.py` or `synce.py` as production services until their missing modules, authentication model, data handling, and dependencies have been independently implemented and tested. The medical integration must not be exposed publicly without a proper identity, authorization, privacy, and audit design.

### Local verification

Python:
```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/validate_json.py
python scripts/validate_domains.py
python -m compileall -q app.py server.py agent.py apps.py synce.py tests scripts
python -m pytest -q
```

Node website preview (Node.js 20+):
```sh
npm test
npm start
```

.NET alternative:
```sh
dotnet restore bd-king-orchestrator.csproj
dotnet build bd-king-orchestrator.csproj --configuration Release
```

The .NET API requires the environment variable `Orchestrator__Token`; there is no default token. The Python Compose service requires `ORCHESTRATOR_TOKEN`. Use different strong random values for different services.

### Deployment boundaries

- The Compose stack starts the Python API only. It does not provision Nginx, DNS, TLS, Tor, PostgreSQL, or the legacy applications.
- The Node server is a local static-site preview; production Nginx serves the website files directly.
- The .NET API is an alternative service, not automatically deployed by the Python Compose stack.
- `Dns/db.tamanna.io` contains documentation-only TEST-NET addresses. Replace them with assigned public addresses before publishing DNS; do not use the sample zone as live DNS.
- The root-level `deply.yml` is not an active GitHub Actions workflow. Review its target paths and deletion behavior before using any manual deployment process.
- A successful CI run validates the checked-in tests and build steps only. It does not prove that the live website, DNS, TLS, server, or data backups work.
