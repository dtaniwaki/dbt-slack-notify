"""Tests for dbt_slack_notify.state."""

import json
from pathlib import Path

from dbt_slack_notify.state import load_state, update_state


class TestLoadState:
    def test_missing_file(self, tmp_state_file: Path) -> None:
        assert load_state(tmp_state_file) == {}

    def test_valid_file(self, tmp_state_file: Path) -> None:
        tmp_state_file.write_text(json.dumps({"thread_ts": "123"}))
        state = load_state(tmp_state_file)
        assert state["thread_ts"] == "123"

    def test_invalid_json(self, tmp_state_file: Path) -> None:
        tmp_state_file.write_text("{bad")
        assert load_state(tmp_state_file) == {}


class TestUpdateState:
    def test_create_new(self, tmp_state_file: Path) -> None:
        update_state({"key": "value"}, tmp_state_file)
        state = json.loads(tmp_state_file.read_text())
        assert state["key"] == "value"

    def test_merge(self, tmp_state_file: Path) -> None:
        tmp_state_file.write_text(json.dumps({"a": 1}))
        update_state({"b": 2}, tmp_state_file)
        state = json.loads(tmp_state_file.read_text())
        assert state["a"] == 1
        assert state["b"] == 2

    def test_overwrite_key(self, tmp_state_file: Path) -> None:
        tmp_state_file.write_text(json.dumps({"a": 1}))
        update_state({"a": 99}, tmp_state_file)
        state = json.loads(tmp_state_file.read_text())
        assert state["a"] == 99
