import json
import os

from app import app
from bridge import BridgeMessage

MCP_TOKEN = "mcp-test-token-" + ("m" * 48)
SERVICE_TOKEN = "service-test-token-" + ("s" * 48)

def headers(token):
    return {"Authorization": "Bearer " + token}

def test_mcp_requires_auth(monkeypatch):
    monkeypatch.setenv("MCP_BEARER_TOKEN", MCP_TOKEN)
    response = app.test_client().post("/mcp", json={"jsonrpc":"2.0","id":1,"method":"tools/list"})
    assert response.status_code == 401

def test_mcp_initialize_and_tools_list(monkeypatch):
    monkeypatch.setenv("MCP_BEARER_TOKEN", MCP_TOKEN)
    client = app.test_client()
    init = client.post("/mcp", json={"jsonrpc":"2.0","id":1,"method":"initialize"}, headers=headers(MCP_TOKEN))
    assert init.status_code == 200
    assert init.get_json()["result"]["serverInfo"]["name"] == "tamanna-bridge"
    tools = client.post("/mcp", json={"jsonrpc":"2.0","id":2,"method":"tools/list"}, headers=headers(MCP_TOKEN))
    assert {x["name"] for x in tools.get_json()["result"]["tools"]} == {"send_user_message","wait_for_tamanna_reply"}

def test_message_round_trip_and_idempotency(monkeypatch):
    monkeypatch.setenv("MCP_BEARER_TOKEN", MCP_TOKEN)
    monkeypatch.setenv("TAMANNA_BRIDGE_SERVICE_TOKEN", SERVICE_TOKEN)
    client = app.test_client()
    payload = {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"send_user_message","arguments":{"text":"hello Tamanna","conversation_id":"ci-conversation","idempotency_key":"ci-key-00000001"}}}
    first = client.post("/mcp", json=payload, headers=headers(MCP_TOKEN)).get_json()
    second = client.post("/mcp", json=payload, headers=headers(MCP_TOKEN)).get_json()
    one = json.loads(first["result"]["content"][0]["text"])
    two = json.loads(second["result"]["content"][0]["text"])
    assert one["message_id"] == two["message_id"]
    assert two["duplicate_submission"] is True
    consumed = client.post("/bridge/v1/consume", json={}, headers=headers(SERVICE_TOKEN))
    assert consumed.status_code == 200
    msg = consumed.get_json()
    assert msg["text"] == "hello Tamanna"
    reply = client.post("/bridge/v1/reply", json={"message_id":msg["message_id"],"reply":"Hello from Tamanna"}, headers=headers(SERVICE_TOKEN))
    assert reply.status_code == 200
    result = client.post("/mcp", json={"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"wait_for_tamanna_reply","arguments":{"message_id":msg["message_id"]}}}, headers=headers(MCP_TOKEN)).get_json()
    answer = json.loads(result["result"]["content"][0]["text"])
    assert answer["status"] == "completed"
    assert answer["reply"] == "Hello from Tamanna"

def test_service_reply_requires_auth(monkeypatch):
    monkeypatch.setenv("TAMANNA_BRIDGE_SERVICE_TOKEN", SERVICE_TOKEN)
    response = app.test_client().post("/bridge/v1/consume", json={})
    assert response.status_code == 401
