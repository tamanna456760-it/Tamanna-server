# Tamanna ChatGPT Communication Bridge

Owner / Configuration Authority: HM INSAN ALI

## Purpose
Provide an explicitly authorized, auditable, two-way message bridge between a ChatGPT custom MCP connection and Tamanna AI. This is not a hidden bypass and does not grant access to ChatGPT internals, private model data, or other users' data.

## Target flow
1. The user sends a message in ChatGPT.
2. ChatGPT invokes an exposed Tamanna MCP tool (for example, `send_user_message`) when the user asks it to communicate with Tamanna.
3. The bridge authenticates the caller, validates the schema and size, assigns a message ID, and places the message in a durable queue.
4. Tamanna AI consumes the message, processes it under its own authorization and safety rules, and posts a correlated response.
5. ChatGPT invokes `wait_for_tamanna_reply` / `get_message` and presents Tamanna's response to the user.

The reverse direction is available only when ChatGPT is actively connected and invokes the retrieval tool. A GitHub repository alone cannot push a message into an already-open ChatGPT conversation.

## Required MCP tools
- `send_user_message(text, conversation_id, idempotency_key)`: enqueue a user instruction.
- `get_message(message_id)`: retrieve delivery/processing state.
- `wait_for_tamanna_reply(message_id, timeout_seconds)`: return the correlated Tamanna response.
- `tamanna_send_reply(message_id, text)`: authenticated Tamanna-to-bridge reply (server-side API; never exposed to arbitrary public callers).
- `bridge_health()`: report readiness without exposing secrets.

## Security requirements
- HTTPS only outside localhost; never expose the bridge over plain HTTP or Tor without end-to-end TLS/authentication.
- OAuth or platform-supported MCP authentication for the ChatGPT-to-MCP connection; separate service identity for Tamanna.
- Keep HMAC-SHA256 service authentication for internal Tamanna service calls, with shared Redis nonce storage in production.
- Store credentials only in deployment secret storage / private environment variables. Never commit tokens, API keys, private keys, or .env files.
- Per-user and per-conversation authorization; strict message size/rate limits; schema validation; idempotency; expiry; audit metadata; encrypted storage and retention controls.
- Treat message text as untrusted data. Never execute instructions embedded in messages as shell commands or grant repository write access implicitly.
- Require owner approval for destructive actions, secret changes, production deployment, or permission escalation.

## Deployment and connection steps
1. Deploy the MCP service on a publicly reachable HTTPS URL.
2. Configure its authentication and allowed ChatGPT account/workspace using the supported ChatGPT MCP connector flow.
3. Configure Tamanna's private service credentials and queue/database.
4. Run end-to-end tests: authenticated send, Tamanna consume, correlated reply, replay rejection, unauthorized rejection, duplicate idempotency, and service restart recovery.
5. Only after the user completes the ChatGPT-side connector setup can the live two-way conversation path be tested.

## Current implementation status
- Existing internal HMAC report protocol is present.
- A canonical-message newline incompatibility in the server signer/verifier was found and corrected in this repository.
- This document is an integration contract, not proof that a live ChatGPT MCP connection or deployed message relay exists.
- No ChatGPT platform bypass, automatic transcript interception, or hidden background channel is implemented.
