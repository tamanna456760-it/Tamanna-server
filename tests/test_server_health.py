import app as server


def test_health_endpoint_is_public_and_minimal():
    response = server.app.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "service": "tamanna-central-server",
    }


def test_report_requires_authentication():
    response = server.app.test_client().post(
        "/api/report", json={"agent_id": "test"}
    )
    assert response.status_code in (401, 503)
