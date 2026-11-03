import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import server_preflight


class PreflightTests(unittest.TestCase):
    def test_rejects_missing_env_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
            with patch.object(server_preflight, "ROOT", root), patch.object(server_preflight.shutil, "which", return_value="/usr/bin/docker"), patch("subprocess.run") as run:
                run.return_value.returncode = 0
                self.assertEqual(server_preflight.main(), 1)

    def test_accepts_strong_token_and_compose_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
            (root / ".env").write_text("ORCHESTRATOR_TOKEN=" + "x" * 48 + "\n", encoding="utf-8")
            with patch.object(server_preflight, "ROOT", root), patch.object(server_preflight.shutil, "which", return_value="/usr/bin/docker"), patch("subprocess.run") as run:
                run.return_value.returncode = 0
                self.assertEqual(server_preflight.main(), 0)


if __name__ == "__main__":
    unittest.main()
