import json
import time

import security.service_protocol as protocol
from app import app


def setup_function():
    protocol._NONCES.clear()


def signed_headers(method, path, body, nonce="nonce_value_123456789"):
    timestamp = str(int(time.time()))
    signature = protocol.sign_request(method, path, timestamp, nonce, body, protocol.SHARED_SECRET)
    return {
        "Content-Type": "application/json",
        "X-Tamanna-Protocol": "1",
        "X-Tamanna-Key-Id": protocol.KEY_ID,
        "X-Tamanna-Timestamp": timestamp,
        "X-Tamanna-Nonce": nonce,
        "X-Tamanna-Signature": signature,
    }


def test_protocol_rejects_missing_shared_secret(monkeypatch):
    monkeypatch.setattr(protocol, "SHARED_SECRET", "")
    assert not protocol.verify_request("POST", "/protocol/v1/report", {}, b"{}")


def test_protocol_accepts_valid_signature(monkeypatch):
    monkeypatch.setattr(protocol, "SHARED_SECRET", "s" * 64)
    body = b'{"agent_id":"tamanna-ai"}'
    headers = signed_headers("POST", "/protocol/v1/report", body)
    assert protocol.verify_request("POST", "/protocol/v1/report", headers, body)


def test_protocol_rejects_replayed_nonce(monkeypatch):
    monkeypatch.setattr(protocol, "SHARED_SECRET", "s" * 64)
    body = b'{"agent_id":"tamanna-ai"}'
    headers = signed_headers("POST", "/protocol/v1/report", body)
    assert protocol.verify_request("POST", "/protocol/v1/report", headers, body)
    assert not protocol.verify_request("POST", "/protocol/v1/report", headers, body)


def test_protocol_rejects_tampered_body(monkeypatch):
    monkeypatch.setattr(protocol, "SHARED_SECRET", "s" * 64)
    body = b'{"agent_id":"tamanna-ai"}'
    headers = signed_headers("POST", "/protocol/v1/report", body)
    assert not protocol.verify_request("POST", "/protocol/v1/report", headers, body + b" ")


def test_protocol_rejects_wrong_path(monkeypatch):
    monkeypatch.setattr(protocol, "SHARED_SECRET", "s" * 64)
    body = b'{"agent_id":"tamanna-ai"}'
    headers = signed_headers("POST", "/protocol/v1/report", body)
    assert not protocol.verify_request("POST", "/protocol/v1/other", headers, body)


def test_protocol_info_is_public_and_does_not_disclose_secret():
    response = app.test_client().get("/protocol/v1")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["protocol"] == "tamanna-service/1"
    assert payload["authentication"] == "HMAC-SHA256"
    assert "secret" not in json.dumps(payload).lower()


def test_protocol_report_requires_signature():
    response = app.test_client().post("/protocol/v1/report", json={"agent_id": "tamanna-ai"})
    assert response.status_code == 401


def test_configured_redis_uses_atomic_nonce_claim(monkeypatch):
    class FakeRedis:
        def __init__(self):
            self.claimed = set()

        def set(self, key, value, nx=False, ex=None):
            if nx and key in self.claimed:
                return None
            self.claimed.add(key)
            return True

    fake = FakeRedis()

    class FakeRedisClient:
        @staticmethod
        def from_url(*args, **kwargs):
            return fake

    class FakeRedisModule:
        Redis = FakeRedisClient

    import sys
    monkeypatch.setitem(sys.modules, "redis", FakeRedisModule)
    monkeypatch.setattr(protocol, "REDIS_URL", "redis://fake/0")
    assert protocol._claim_nonce("tamanna-ai", "nonce_redis_123456789", int(time.time()))
    assert not protocol._claim_nonce("tamanna-ai", "nonce_redis_123456789", int(time.time()))


def test_configured_redis_fails_closed_when_unavailable(monkeypatch):
    import sys
    class BrokenRedisModule:
        @staticmethod
        def from_url(*args, **kwargs):
            raise ConnectionError("unavailable")
    monkeypatch.setitem(sys.modules, "redis", BrokenRedisModule)
    monkeypatch.setattr(protocol, "REDIS_URL", "redis://unavailable/0")
    assert not protocol._claim_nonce("tamanna-ai", "nonce_redis_987654321", int(time.time()))
