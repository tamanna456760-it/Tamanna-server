import json
from types import SimpleNamespace

import pytest

from scripts import validate_json


def test_duplicate_json_keys_are_rejected():
    with pytest.raises(ValueError, match="duplicate object key"):
        json.loads('{"name":"first","name":"second"}',
                   object_pairs_hook=validate_json.reject_duplicate_keys)


def test_distinct_json_keys_are_accepted():
    parsed = json.loads(
        '{"name":"Tamanna","version":1}',
        object_pairs_hook=validate_json.reject_duplicate_keys,
    )
    assert parsed == {"name": "Tamanna", "version": 1}


def test_git_nul_separated_paths_are_parsed(monkeypatch, tmp_path):
    monkeypatch.setattr(validate_json, "ROOT", tmp_path)
    first = tmp_path / "one.json"
    second = tmp_path / "folder with spaces" / "two.json"
    second.parent.mkdir()
    first.write_text("{}", encoding="utf-8")
    second.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        validate_json.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout=b"one.json\0folder with spaces/two.json\0"
        ),
    )

    assert validate_json.tracked_json_files() == [first, second]
