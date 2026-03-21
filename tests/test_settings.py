"""Tests for dbt_slack_notify.settings."""

import tempfile
from pathlib import Path

import pytest

from dbt_slack_notify.settings import Settings


class TestSettings:
    def test_defaults(self) -> None:
        settings = Settings()
        assert settings.slack_token is None
        assert settings.slack_channel is None
        assert settings.dbt_project_dir == "."
        assert settings.dbt_target_path == "target"
        assert settings.log_level == "INFO"
        assert settings.log_file is None
        expected_state_file = str(Path(tempfile.gettempdir()) / "dbt_slack_notify_state.json")
        assert settings.state_file == expected_state_file

    def test_prefixed_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DBT_SLACK_NOTIFY_SLACK_TOKEN", "xoxb-prefixed")
        monkeypatch.setenv("DBT_SLACK_NOTIFY_SLACK_CHANNEL", "#prefixed")
        monkeypatch.setenv("DBT_SLACK_NOTIFY_DBT_PROJECT_DIR", "/proj")
        monkeypatch.setenv("DBT_SLACK_NOTIFY_DBT_TARGET_PATH", "out")
        monkeypatch.setenv("DBT_SLACK_NOTIFY_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("DBT_SLACK_NOTIFY_LOG_FILE", "/var/log/dbt.log")
        monkeypatch.setenv("DBT_SLACK_NOTIFY_STATE_FILE", "/tmp/custom.json")
        settings = Settings()
        assert settings.slack_token == "xoxb-prefixed"
        assert settings.slack_channel == "#prefixed"
        assert settings.dbt_project_dir == "/proj"
        assert settings.dbt_target_path == "out"
        assert settings.log_level == "DEBUG"
        assert settings.log_file == "/var/log/dbt.log"
        assert settings.state_file == "/tmp/custom.json"

    def test_unprefixed_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SLACK_TOKEN", "xoxb-fallback")
        monkeypatch.setenv("SLACK_CHANNEL", "#fallback")
        monkeypatch.setenv("DBT_PROJECT_DIR", "/fallback")
        settings = Settings()
        assert settings.slack_token == "xoxb-fallback"
        assert settings.slack_channel == "#fallback"
        assert settings.dbt_project_dir == "/fallback"

    def test_prefixed_overrides_unprefixed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SLACK_TOKEN", "xoxb-unprefixed")
        monkeypatch.setenv("DBT_SLACK_NOTIFY_SLACK_TOKEN", "xoxb-prefixed")
        settings = Settings()
        assert settings.slack_token == "xoxb-prefixed"
