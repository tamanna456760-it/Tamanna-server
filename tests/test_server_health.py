import app as server

TEST_TOKEN = "tamanna-ci-token-" + ("x" * 48)
WRONG_TOKEN = "wrong-ci-token-" + ("y" * 48)


def setup_function():
    server._rate_events.clear()


def test_health_endpoint_is_public_and_minimal():
    response = server.app.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "service": "tamanna-central-server"}


def test_readiness_checks_database():
    response = server.app.test_client().get("/health/ready")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ready", "database": "ok"}


def test_public_root_does_not_expose_reports():
    response = server.app.test_client().get("/")
    assert response.status_code == 200
    assert response.get_json()["service"] == "Tamanna Central Server"
    assert "reports" not in response.get_json()


def test_report_requires_authentication():
    response = server.app.test_client().post("/api/report", json={"agent_id": "test"})
    assert response.status_code in (401, 503)


def test_report_rejects_weak_server_token(monkeypatch):
    monkeypatch.setattr(server, "API_TOKEN", "weak-token")
    response = server.app.test_client().post(
        "/api/report", json={"agent_id": "test"},
        headers={"Authorization": "Bearer weak-token"},
    )
    assert response.status_code == 503


def test_report_body_size_limit(monkeypatch):
    monkeypatch.setitem(server.app.config, "MAX_CONTENT_LENGTH", 8)
    monkeypatch.setattr(server, "API_TOKEN", TEST_TOKEN)
    response = server.app.test_client().post(
        "/api/report", data='{"agent_id":"too-long"}', content_type="application/json",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 413


def test_report_rejects_wrong_token(monkeypatch):
    monkeypatch.setattr(server, "API_TOKEN", TEST_TOKEN)
    response = server.app.test_client().post(
        "/api/report", json={"agent_id": "test"},
        headers={"Authorization": f"Bearer {WRONG_TOKEN}"},
    )
    assert response.status_code == 403


def test_report_accepts_valid_token(monkeypatch):
    monkeypatch.setattr(server, "API_TOKEN", TEST_TOKEN)
    response = server.app.test_client().post(
        "/api/report", json={"agent_id": "test", "branch": "test"},
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 201
    assert response.get_json()["status"] == "ok"


def test_report_rejects_non_json_content(monkeypatch):
    monkeypatch.setattr(server, "API_TOKEN", TEST_TOKEN)
    response = server.app.test_client().post(
        "/api/report", data="agent_id=test", content_type="text/plain",
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 415


def test_report_rejects_invalid_payload(monkeypatch):
    monkeypatch.setattr(server, "API_TOKEN", TEST_TOKEN)
    response = server.app.test_client().post(
        "/api/report", json={"agent_id": ""},
        headers={"Authorization": f"Bearer {TEST_TOKEN}"},
    )
    assert response.status_code == 400


def test_reports_endpoint_requires_authentication():
    response = server.app.test_client().get("/api/reports")
    assert response.status_code in (401, 503)


def test_reports_endpoint_accepts_valid_token(monkeypatch):
    monkeypatch.setattr(server, "API_TOKEN", TEST_TOKEN)
    response = server.app.test_client().get(
        "/api/reports", headers={"Authorization": f"Bearer {TEST_TOKEN}"}
    )
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)


def test_security_headers_are_present():
    response = server.app.test_client().get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Cache-Control"] == "no-store"


def test_cors_only_allows_configured_origins(monkeypatch):
    monkeypatch.setattr(server, "CORS_ORIGINS", {"https://www.bd-king-r7.com"})
    client = server.app.test_client()
    allowed = client.get("/health", headers={"Origin": "https://www.bd-king-r7.com"})
    blocked = client.get("/health", headers={"Origin": "https://evil.example"})
    assert allowed.headers["Access-Control-Allow-Origin"] == "https://www.bd-king-r7.com"
    assert "Access-Control-Allow-Origin" not in blocked.headers


def test_api_rate_limit(monkeypatch):
    monkeypatch.setattr(server, "RATE_LIMIT_PER_MINUTE", 1)
    client = server.app.test_client()
    assert client.get("/api/reports").status_code in (401, 503)
    assert client.get("/api/reports").status_code == 429

    
def test_protocol_endpoint_is_rate_limited_before_authentication(monkeypatch):
    monkeypatch.setattr(server, "RATE_LIMIT_PER_MINUTE", 1)
    client = server.app.test_client()
    first = client.post("/protocol/v1/report", json={"agent_id": "test"})
    second = client.post("/protocol/v1/report", json={"agent_id": "test"})
    assert first.status_code == 401
    assert second.status_code == 429
