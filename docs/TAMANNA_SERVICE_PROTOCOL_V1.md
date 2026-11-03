# Tamanna Service Protocol v1

This is the service-to-service contract between Tamanna AI and Tamanna Central Server. It is separate from browser login and from the existing bearer-token API.

## Endpoints

- Discovery: GET /protocol/v1 (public protocol metadata only)
- Signed report: POST /protocol/v1/report
- Content type: application/json
- Protocol header: X-Tamanna-Protocol: 1
- Key ID: X-Tamanna-Key-Id: tamanna-ai (must match server configuration)

## Shared secret

Set the same randomly generated secret in both private, untracked .env files:

- Central Server: TAMANNA_SERVICE_SHARED_SECRET
- Tamanna AI: TAMANNA_SERVER_SHARED_SECRET

Generate at least 32 random bytes (64 hexadecimal characters) locally with:

    openssl rand -hex 32

Never put the secret in GitHub, chat messages, logs, URLs, or browser code. Use different secrets for staging and production.

Central Server also configures TAMANNA_SERVICE_KEY_ID and TAMANNA_PROTOCOL_CLOCK_SKEW_SECONDS.

## Signed request

Tamanna AI sends these headers:

- X-Tamanna-Protocol
- X-Tamanna-Key-Id
- X-Tamanna-Timestamp: Unix seconds
- X-Tamanna-Nonce: unique random URL-safe value, at least 16 characters
- X-Tamanna-Signature: lowercase hex HMAC-SHA256

The signature is calculated over UTF-8 canonical text, with newline separators and no trailing newline:

    1
    UPPERCASE_HTTP_METHOD
    EXACT_PATH
    UNIX_TIMESTAMP
    UNIQUE_NONCE
    LOWERCASE_SHA256_HEX_OF_EXACT_BODY_BYTES

Then calculate HMAC-SHA256(shared_secret, canonical_text) and hex-encode it. The exact transmitted body bytes must be the bytes that were signed. The server rejects wrong versions, key IDs, stale timestamps, malformed signatures, invalid signatures, and replayed nonces.

## Report payload

    {
      "agent_id": "tamanna-ai",
      "branch": "main",
      "build_ok": true,
      "committed": false,
      "commit_sha": "optional-git-commit-sha"
    }

Success is HTTP 201 with status, id, and protocol in JSON. Authentication failures return HTTP 401. Do not retry using the same nonce; generate a fresh nonce and signature for every attempt.

## Security and deployment requirements

- Use HTTPS on public networks. Onion transport is not a substitute for application authentication.
- Keep the Central Server bound to its private interface; expose it only through a trusted reverse proxy or private network.
- Synchronize clocks (NTP); default allowed skew is 300 seconds.
- Rotate shared secrets deliberately on both services.
- Restrict each service identity to only the endpoints it needs.
- Docker Compose configures an internal Redis service and the server uses atomic Redis SET NX with an expiry for replay protection across workers. Redis is not published to the host. If Redis is configured but unavailable, authentication fails closed. Local development without Redis falls back to a process-local nonce cache; do not use that fallback for multi-worker or multi-host production.
- Add rate limiting at the reverse proxy/WAF for production. The existing Flask API limiter is per-process and not a substitute for distributed edge controls.
- Do not send passwords, user chat content, API keys, or private account data in report payloads.

Protocol v1 currently authenticates service reports only. It does not grant remote shell, code execution, deployment, account administration, or arbitrary database access.
