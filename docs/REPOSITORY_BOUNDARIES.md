# Tamanna-server — Repository Ownership and Cleanup Plan

## Purpose

Tamanna-server is the central backend/server repository for the Tamanna ecosystem. It owns API runtime, identity/security, model adapters, persistence, operational scripts, monitoring, backup and deployment.

It must not become the public website repository. Public website source belongs in `tamanna456760-it/tamanna-website` (the existing website repository). The previously referenced `tamanna-wabside` repository is not currently present as an accessible repository. The main Tamanna- repository remains the product/client and shared AI application source.

## Intended server layout

~~~text
Tamanna-server/
├── README.md
├── main.py                    # canonical server entrypoint
├── tamanna_server/
│   ├── api/
│   ├── core/
│   ├── identity/
│   ├── security/
│   ├── ai/
│   ├── agents/
│   ├── database/
│   ├── storage/
│   ├── monitoring/
│   ├── audit/
│   └── backup/
├── config/                    # safe defaults only
├── migrations/
├── tests/
├── scripts/
├── deploy/
│   ├── nginx/
│   └── tor/
├── docs/
├── data/                      # runtime-only, ignored
├── logs/                      # runtime-only, ignored
├── .github/workflows/
├── .env.example
├── .gitignore
├── Dockerfile
└── docker-compose.yml
~~~

This is a target structure, not a claim that the current repository already matches it. Existing entrypoints and modules must be mapped before moving anything.

## Confirmed tree-level cleanup candidates

The current main-branch root contains a large mixture of Python, JavaScript, shell, Android/Gradle, .NET/C# files, compiled DLL/PDB/cache/build artifacts, database/report files and a Wabsite directory. This conflicts with the intended server-only repository boundary. The actual website repository is `tamanna-website`; `Wabsite/` is still present here because the current deployment guide and server workflows refer to it. Treat it as a deployment copy until the publish/sync path is verified.

Do not delete or move these by filename alone:
- Wabsite directory: identify whether it is deployed and whether any workflows/build contexts refer to it.
- DLL, PDB, generated C# and NuGet/Gradle build outputs: confirm whether source/build artifacts are required for a current deployment or can be reproduced.
- .pyc, reports.db and generated caches: inspect tracking and references; runtime state should not be versioned.
- Multiple root entrypoints and scripts: identify the canonical launch path and preserve compatibility until tests prove migration safe.

## Rules

1. Keep production secrets and .env files out of Git.
2. Use one canonical Python server entrypoint; document compatibility wrappers.
3. Keep website assets out of this repository after a verified migration to the website repo.
4. Keep generated binaries and runtime databases out of source control unless a documented release artifact requires them.
5. Use tests and import/reference scans before every move.
6. Quarantine before deletion, preserve original path and blob SHA, and keep a rollback path.
7. Deploy only from reviewed, tested commits with least-privilege credentials.
8. The local model endpoint must not be exposed publicly.

## Verification status

This document records repository ownership and a tree-level audit only. No server runtime, Docker deployment, production DNS, API route or restore test was executed as part of this documentation change.


## 2026-11-15 inventory update

A fresh recursive tree inspection found 292 tracked paths. A broad generated-artifact scan flagged 34 paths, including root-level .NET DLL/PDB and MSBuild outputs, one Python bytecode file, and `reports.db`. These are candidates for dependency review, not automatically safe to move: the repository contains a .NET project and deployment/build definitions that must be checked first. The `dockerfile` currently builds the Python `app:app` service, while `docker-compose.yml` also builds the separate AI image. Do not relocate root entrypoints, `vendor/tamanna-ai`, `Wabsite/`, or project outputs until all workflow, Docker, import, and runtime references are traced.

The website-only repository is `tamanna456760-it/tamanna-website` (31 tracked paths at this audit). Keep its HTML, CSS, JavaScript, PWA assets, knowledge JSON, and website tests together there. `Tamanna-server/Wabsite/` remains a deployment copy pending verified synchronization.

No files were moved or deleted during this inventory update. The next safe migration unit is one identified file group with a complete reference scan, a reversible quarantine record, and a passing relevant CI run.
