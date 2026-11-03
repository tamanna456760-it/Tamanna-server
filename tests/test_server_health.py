import app as server


def test_health_endpoint_is_public_and_minimal():
    response = server.app.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "service": "tamanna-central-server",
    }


def test_public_root_does_not_expose_reports():
    response = server.app.test_client().get("/")
    assert response.status_code == 200
    assert response.get_json()["service"] == "Tamanna Central Server"
    assert "reports" not in response.get_json()


def test_report_requires_authentication():
    response = server.app.test_client().post(
        "/api/report", json={"agent_id": "test"}
    )
    assert response.status_code in (401, 503)


def test_report_rejects_wrong_token(monkeypatch):
    monkeypatch.setattr(server, "API_TOKEN", "expected-token")
    response = server.app.test_client().post(
        "/api/report",
        json={"agent_id": "test"},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert response.status_code == 403


def test_report_accepts_valid_token(monkeypatch):
    monkeypatch.setattr(server, "API_TOKEN", "ci-test-token")
    response = server.app.test_client().post(
        "/api/report",
        json={"agent_id": "test", "branch": "test"},
        headers={"Authorization": "Bearer ci-test-token"},
    )
    assert response.status_code == 201
    assert response.get_json() == {"status": "ok"}


def test_reports_endpoint_requires_authentication():
    response = server.app.test_client().get("/api/reports")
    assert response.status_code in (401, 503)


def test_security_headers_are_present():
    response = server.app.test_client().get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
