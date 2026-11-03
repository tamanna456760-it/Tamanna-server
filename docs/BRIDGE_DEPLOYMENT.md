# Deploying the Tamanna Two-Way Bridge

Owner / Configuration Authority: HM INSAN ALI

## Components
- Central Server `/mcp`: stateless JSON-RPC MCP endpoint with `initialize`, `tools/list`, and `tools/call`.
- MCP tools: `send_user_message` and `wait_for_tamanna_reply`.
- Worker endpoints: `POST /bridge/v1/consume` and `POST /bridge/v1/reply`.
- Durable `bridge_messages` SQL table stores message state and correlated replies.
- Tamanna AI adapter: `tamanna_ai/integrations/bridge_worker.py`.

## Private environment configuration
Generate independent secrets (do not reuse the existing report protocol key):

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Set in the Central Server private `.env`:

```env
MCP_BEARER_TOKEN=<first-random-secret>
TAMANNA_BRIDGE_SERVICE_TOKEN=<second-random-secret>
BRIDGE_MAX_MESSAGE_CHARS=12000
```

Set in Tamanna AI private `.env`:

```env
TAMANNA_BRIDGE_URL=https://YOUR-CENTRAL-SERVER
TAMANNA_BRIDGE_SERVICE_TOKEN=<same-second-random-secret>
```

Never commit real values. Use HTTPS for every non-local connection. The MCP bearer token is an initial bearer-auth option; production ChatGPT connector deployment should use the platform-supported authenticated custom MCP connection / OAuth flow where available, with a per-user authorization mapping.

## ChatGPT-side connector
Expose the Central Server at a public HTTPS URL, then add the MCP endpoint URL ending in `/mcp` through the supported ChatGPT custom MCP connector setup. Configure the MCP credential using the first secret only if the selected connector flow supports bearer credentials. The user must complete the connector authorization in ChatGPT. A GitHub commit cannot perform that UI authorization.

## Worker integration
Construct `TamannaBridgeWorker(handler=your_safe_chat_handler)` in the Tamanna AI worker process and call `process_one()` from a supervised polling loop. The handler must call the existing Tamanna chat/model service; this adapter does not invent a model or bypass model authentication. Do not map message text to shell execution, arbitrary code execution, or unapproved GitHub writes.

## Verification
Run `pytest -q tests/test_bridge.py tests/test_server_health.py` in the Central Server environment. Then perform a live test only after deploying both services and authorizing the ChatGPT connector.

## Limitations / hardening before production
- Queue persistence uses the configured SQL database; use PostgreSQL for multi-instance production.
- Add message expiry, retry/dead-letter handling, per-user authorization, and distributed rate limiting before broad exposure.
- The current worker marks a message as processing; automatic lease recovery is not implemented yet.
- ChatGPT only receives Tamanna replies when it invokes `wait_for_tamanna_reply`; this is not an automatic background push into an open conversation.
- No OpenAI private data, hidden model access, or platform bypass is used.