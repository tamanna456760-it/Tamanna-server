import subprocess

import pytest

from agent import Agent, run, safe_relative_path


def test_command_runner_does_not_invoke_shell(tmp_path):
    marker = tmp_path / "should-not-exist"
    rc, output = run(
        f"printf 'safe; touch {marker}'",
        cwd=tmp_path,
    )
    assert rc == 0
    assert output == f"safe; touch {marker}"
    assert not marker.exists()


def test_safe_relative_path_rejects_parent_traversal():
    with pytest.raises(ValueError):
        safe_relative_path("../outside.txt", "marker")


def test_agent_rejects_invalid_branch(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    with pytest.raises(ValueError, match="branch"):
        Agent({
            "repo_path": str(repo),
            "branch": "--upload-pack=malicious",
            "lockfile": str(tmp_path / "agent.lock"),
            "logfile": str(tmp_path / "agent.log"),
        })


def test_agent_refuses_to_reset_dirty_working_tree(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
    marker = repo / "user-work.txt"
    marker.write_text("preserve me", encoding="utf-8")
    agent = Agent({
        "repo_path": str(repo),
        "branch": "powerhub-auto",
        "remote": "origin",
        "lockfile": str(tmp_path / "agent.lock"),
        "logfile": str(tmp_path / "agent.log"),
    })

    agent.perform_run()

    assert marker.read_text(encoding="utf-8") == "preserve me"
    assert not (tmp_path / "agent.lock").exists()
