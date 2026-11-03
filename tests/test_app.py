import os
import unittest

os.environ["ORCHESTRATOR_TOKEN"] = "ci-only-token"
os.environ["DATABASE_URL"] = "sqlite://"

from app import app  # noqa: E402


class TamannaAppTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_health_is_public_and_healthy(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_report_endpoint_rejects_missing_token(self):
        response = self.client.post("/api/report", json={"agent_id": "ci"})
        self.assertEqual(response.status_code, 401)

    def test_dashboard_requires_authentication(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 401)

    def test_report_accepts_valid_token_and_json(self):
        response = self.client.post(
            "/api/report",
            json={"agent_id": "ci", "branch": "test", "build_ok": True},
            headers={"Authorization": "Bearer ci-only-token"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json(), {"status": "ok"})

    def test_report_rejects_non_object_json(self):
        response = self.client.post(
            "/api/report",
            data='["not", "an", "object"]',
            content_type="application/json",
            headers={"Authorization": "Bearer ci-only-token"},
        )
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
