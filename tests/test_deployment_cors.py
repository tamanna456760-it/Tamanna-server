from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DeploymentCorsConfigurationTests(unittest.TestCase):
    def test_compose_allows_github_pages_guest_chat_origin(self):
        compose = (ROOT / "docker-compose.yml").read_text()
        self.assertIn(
            "TAMANNA_CORS_ORIGINS: \"\u0024{TAMANNA_CORS_ORIGINS:-https://www.bd-king-r7.com,https://bd-king-r7.com,https://tamanna456760-it.github.io}\"",
            compose,
        )

    def test_vps_bootstrap_sets_the_variable_consumed_by_ai_backend(self):
        setup = (ROOT / "deploy/vps-setup.sh").read_text()
        self.assertIn("set_env TAMANNA_CORS_ORIGINS ", setup)
        self.assertIn("https://tamanna456760-it.github.io", setup)
        self.assertNotIn('set_env CORS_ORIGINS ', setup)


if __name__ == "__main__":
    unittest.main()
