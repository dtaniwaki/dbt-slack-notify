"""Application settings resolved from environment variables."""

from __future__ import annotations

import tempfile
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


def _default_state_file() -> str:
    return str(Path(tempfile.gettempdir()) / "dbt_slack_notify_state.json")


class Settings(BaseSettings):
    slack_token: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DBT_SLACK_NOTIFY_SLACK_TOKEN", "SLACK_TOKEN"),
    )
    slack_channel: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DBT_SLACK_NOTIFY_SLACK_CHANNEL", "SLACK_CHANNEL"),
    )
    dbt_project_dir: str = Field(
        default=".",
        validation_alias=AliasChoices("DBT_SLACK_NOTIFY_DBT_PROJECT_DIR", "DBT_PROJECT_DIR"),
    )
    dbt_target_path: str = Field(
        default="target",
        validation_alias=AliasChoices("DBT_SLACK_NOTIFY_DBT_TARGET_PATH", "DBT_TARGET_PATH"),
    )
    log_level: str = Field(
        default="INFO",
        validation_alias=AliasChoices("DBT_SLACK_NOTIFY_LOG_LEVEL", "LOG_LEVEL"),
    )
    log_file: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DBT_SLACK_NOTIFY_LOG_FILE", "LOG_FILE"),
    )
    state_file: str = Field(
        default_factory=_default_state_file,
        validation_alias=AliasChoices("DBT_SLACK_NOTIFY_STATE_FILE", "STATE_FILE"),
    )
