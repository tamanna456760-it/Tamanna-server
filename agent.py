#!/usr/bin/env python3
"""Restricted local automation agent for an explicitly configured Git repository."""
import logging
import os
import re
import shlex
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

LOG = logging.getLogger("bdking_agent")
LOG.setLevel(logging.INFO)
if not LOG.handlers:
    LOG.addHandler(logging.StreamHandler(sys.stdout))

DEFAULT_CONFIG_PATH = "/etc/bdking/agent.yml"
SAFE_NAME = re.compile(r"^[A-Za-z0-9._/-]+$")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def run(cmd, cwd=None, timeout=300):
    """Run an argv command without a shell; shell operators are not supported."""
    argv = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
    if not argv or not all(isinstance(part, str) for part in argv):
        raise ValueError("command must be a non-empty string or argument list")
    LOG.info("RUN: %s (cwd=%s)", shlex.join(argv), cwd)
    try:
        result = subprocess.run(
            argv,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = result.stdout or ""
        if output:
            LOG.debug(output.rstrip())
        return result.returncode, output.rstrip()
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        raise TimeoutError(f"command timed out after {timeout}s: {argv[0]}\n{output}") from exc


def safe_relative_path(value, label):
    path = Path(value)
    if path.is_absolute() or not value or any(part in ("..", "") for part in path.parts):
        raise ValueError(f"{label} must be a safe relative path")
    return path


class Agent:
    def __init__(self, cfg):
        if not isinstance(cfg, dict):
            raise ValueError("agent configuration must be a YAML object")
        self.repo_path = Path(cfg["repo_path"]).expanduser().resolve()
        self.branch = str(cfg.get("branch", "powerhub-auto"))
        self.remote = str(cfg.get("remote", "origin"))
        if not SAFE_NAME.fullmatch(self.branch) or self.branch.startswith("-") or ".." in self.branch:
            raise ValueError("branch contains unsupported characters")
        if not re.fullmatch(r"[A-Za-z0-9._-]+", self.remote) or self.remote.startswith("-"):
            raise ValueError("remote contains unsupported characters")
        self.user = cfg.get("user") or os.environ.get("USER", "nobody")
        self.interval = max(30, int(cfg.get("interval_seconds", 60)))
        push_setting = cfg.get("push_changes", False)
        if not isinstance(push_setting, bool):
            raise ValueError("push_changes must be a YAML boolean")
        self.push_changes = push_setting
        self.fix_cmds = cfg.get("fix_cmds", [])
        self.build_cmds = cfg.get("build_cmds", [])
        if not isinstance(self.fix_cmds, list) or not all(isinstance(x, str) for x in self.fix_cmds):
            raise ValueError("fix_cmds must be a list of command strings")
        if not isinstance(self.build_cmds, list) or not all(isinstance(x, str) for x in self.build_cmds):
            raise ValueError("build_cmds must be a list of command strings")
        self.ficar = safe_relative_path(str(cfg.get("ficar", "ficar")), "ficar")
        self.powersync = safe_relative_path(str(cfg.get("power_sync", "power_sync")), "power_sync")
        self.lockfile = Path(cfg.get("lockfile", "/var/lock/bd-king-r7-powerhub.lock"))
        self.logfile = Path(cfg.get("logfile", "/var/log/bd-king-r7-powerhub.log"))
        self.server_url = cfg.get("server_url", "").rstrip("/")
        self.agent_id = cfg.get("agent_id", str(uuid.uuid4()))
        self.auth_token = os.environ.get("ORCHESTRATOR_TOKEN", "")
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"repo_path is not a Git repository: {self.repo_path}")
        if self.server_url and not self.auth_token:
            raise ValueError("ORCHESTRATOR_TOKEN is required when server_url is configured")

    def _write_log(self, msg):
        self.logfile.parent.mkdir(parents=True, exist_ok=True)
        with self.logfile.open("a", encoding="utf-8") as stream:
            stream.write(f"[{now_iso()}] {msg}\n")

    def acquire_lock(self):
        self.lockfile.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(self.lockfile), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(str(os.getpid()))
            self._write_log("acquired lock")
            return True
        except FileExistsError:
            self._write_log("lock exists, skipping run")
            return False

    def release_lock(self):
        try:
            if self.lockfile.exists():
                self.lockfile.unlink()
                self._write_log("released lock")
        except OSError:
            LOG.exception("release_lock failed")

    def post_report(self, payload):
        if not self.server_url:
            return None
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.auth_token}"}
        try:
            response = requests.post(
                f"{self.server_url}/api/report",
                json=payload,
                headers=headers,
                timeout=15,
            )
            self._write_log(f"report submitted with HTTP {response.status_code}")
            return response.status_code, response.text
        except requests.RequestException as exc:
            self._write_log(f"report submission failed: {type(exc).__name__}")
            return None, "report submission failed"

    def git(self, command, timeout=300):
        args = shlex.split(command) if isinstance(command, str) else list(command)
        return run(["git", *args], cwd=str(self.repo_path), timeout=timeout)

    def perform_run(self):
        self._write_log("run start")
        if not self.acquire_lock():
            return
        try:
            status_rc, status = self.git("status --porcelain")
            if status_rc != 0:
                raise RuntimeError("could not inspect Git working tree")
            if status.strip():
                raise RuntimeError("working tree is dirty; refusing to overwrite local changes")

            rc, _ = self.git("fetch --all --prune")
            if rc != 0:
                raise RuntimeError("git fetch failed")

            rc, _ = self.git(f"rev-parse --verify refs/heads/{self.branch}")
            if rc == 0:
                rc, _ = self.git(f"checkout {self.branch}")
            else:
                remote_rc, _ = self.git(f"ls-remote --exit-code {self.remote} main")
                if remote_rc == 0:
                    rc, _ = self.git(f"checkout -b {self.branch} {self.remote}/main")
                else:
                    rc, _ = self.git(f"checkout -b {self.branch}")
            if rc != 0:
                raise RuntimeError("could not checkout automation branch")

            remote_branch_rc, _ = self.git(f"ls-remote --exit-code {self.remote} {self.branch}")
            if remote_branch_rc == 0:
                pull_rc, _ = self.git(f"pull --ff-only {self.remote} {self.branch}")
                if pull_rc != 0:
                    raise RuntimeError("fast-forward update failed; refusing destructive reset")

            fixer_out = []
            for command in self.fix_cmds:
                if command.strip():
                    rc, output = run(command, cwd=str(self.repo_path))
                    fixer_out.append({"cmd": command, "rc": rc, "out": output})

            build_ok = True
            build_out = []
            for command in self.build_cmds:
                if command.strip():
                    rc, output = run(command, cwd=str(self.repo_path))
                    build_out.append({"cmd": command, "rc": rc, "out": output})
                    if rc != 0:
                        build_ok = False
                        break

            uid = str(uuid.uuid4())
            (self.repo_path / self.ficar).parent.mkdir(parents=True, exist_ok=True)
            (self.repo_path / self.powersync).parent.mkdir(parents=True, exist_ok=True)
            (self.repo_path / self.ficar).write_text(
                f"Updated at: {now_iso()}\nUUID: {uid}\n", encoding="utf-8"
            )
            (self.repo_path / self.powersync).write_text(
                f"Last run: {now_iso()} BUILD_OK={build_ok}\n", encoding="utf-8"
            )
            # Initial clean-tree check means all current changes were created by this run.
            self.git("add -A")

            changes_rc, changes = self.git("status --porcelain")
            if changes_rc != 0:
                raise RuntimeError("could not inspect staged changes")
            has_changes = bool(changes.strip())
            committed = False
            commit_sha = None

            if has_changes and build_ok:
                commit_rc, _ = self.git(["commit", "-m", f"Automated sync/fix/build {now_iso()}"])
                if commit_rc == 0:
                    committed = True
                    sha_rc, sha = self.git("rev-parse --short HEAD")
                    if sha_rc == 0:
                        commit_sha = sha.strip()
                    if self.push_changes:
                        push_rc, _ = self.git(["push", "-u", self.remote, self.branch])
                        self._write_log(f"push rc={push_rc}")
                else:
                    self._write_log("commit failed; changes remain local for review")

            report = {
                "agent_id": self.agent_id,
                "timestamp": now_iso(),
                "repo_path": str(self.repo_path),
                "branch": self.branch,
                "fixer_out": fixer_out,
                "build_ok": build_ok,
                "build_out": build_out,
                "has_changes": has_changes,
                "committed": committed,
                "commit_sha": commit_sha,
            }
            self.post_report(report)
            self._write_log("run finished")
        except Exception as exc:
            LOG.exception("perform_run failed")
            self._write_log(f"run error: {type(exc).__name__}: {exc}")
        finally:
            self.release_lock()

    def run_loop(self):
        self._write_log("agent starting main loop")
        stop = False

        def handle_signal(_signum, _frame):
            nonlocal stop
            stop = True

        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
        while not stop:
            self.perform_run()
            for _ in range(self.interval):
                if stop:
                    break
                time.sleep(1)
        self._write_log("agent exiting")


def load_config(path=DEFAULT_CONFIG_PATH):
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"agent config not found: {config_path}")
    with config_path.open(encoding="utf-8") as stream:
        cfg = yaml.safe_load(stream)
    if not isinstance(cfg, dict):
        raise ValueError("agent config must contain a YAML object")
    return cfg


def main():
    agent = Agent(load_config())
    agent.run_loop()


if __name__ == "__main__":
    main()
