"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

_ENV_KEYS = [
    "SLACK_TOKEN", "SLACK_CHANNEL",
    "DBT_PROJECT_DIR", "DBT_TARGET_PATH",
    "LOG_LEVEL", "LOG_FILE", "STATE_FILE",
]


@pytest.fixture()
def tmp_state_file(tmp_path: Path) -> Path:
    return tmp_path / "state.json"


@pytest.fixture()
def mock_slack_client() -> MagicMock:
    client = MagicMock()
    client.chat_postMessage.return_value = {"ts": "1234567890.123456"}
    return client


@pytest.fixture()
def run_results_path(tmp_path: Path) -> Path:
    return tmp_path / "run_results.json"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove Slack / dbt env vars so tests don't leak."""
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
        monkeypatch.delenv(f"DBT_SLACK_NOTIFY_{key}", raising=False)
