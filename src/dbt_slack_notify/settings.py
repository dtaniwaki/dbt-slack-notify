"""Application settings resolved from environment variables."""

from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


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
        default="/tmp/slack_build_state.json",
        validation_alias=AliasChoices("DBT_SLACK_NOTIFY_STATE_FILE", "STATE_FILE"),
    )
