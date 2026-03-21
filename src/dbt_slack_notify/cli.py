"""Click CLI for dbt-slack-notify."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from dbt_slack_notify.constants import LOG_LEVELS
from dbt_slack_notify.runner import VALID_TYPES, SlackNotifyingRunner
from dbt_slack_notify.settings import Settings


def _configure_logging(level_name: str, log_file: str | None = None) -> None:
    level = LOG_LEVELS.get(level_name.upper(), logging.INFO)
    fmt = "%(levelname)s: %(message)s"
    if log_file:
        logging.basicConfig(level=level, format=fmt, filename=log_file)
    else:
        logging.basicConfig(level=level, format=fmt, stream=sys.stderr)


@click.command(context_settings={"ignore_unknown_options": True})
@click.option(
    "--type", "notification_type",
    type=click.Choice(VALID_TYPES),
    default="auto",
    show_default=True,
    help="Notification type.",
)
@click.option(
    "--label",
    default=None,
    help="Label appended to notification title (e.g. 'Elementary' -> 'dbt test (Elementary)').",
)
@click.option(
    "--slack-thread-ts",
    default=None,
    help="Existing Slack thread timestamp to reply to.",
)
@click.option("--slack-token", default=None, help="Slack API token (overrides env var).")
@click.option("--slack-channel", default=None, help="Slack channel (overrides env var).")
@click.option("--dbt-project-dir", default=None, help="dbt project directory (overrides env var).")
@click.option("--dbt-target-path", default=None, help="dbt target path (overrides env var).")
@click.option(
    "--log-level",
    type=click.Choice(list(LOG_LEVELS.keys()), case_sensitive=False),
    default=None,
    help="Log level (overrides env var, default: INFO).",
)
@click.option("--log-file", default=None, help="Log file path (overrides env var).")
@click.option("--state-file", default=None, help="State file path (overrides env var).")
@click.argument("command", nargs=-1, required=True)
def cli(
    notification_type: str,
    command: tuple[str, ...],
    label: str | None,
    slack_thread_ts: str | None,
    slack_token: str | None,
    slack_channel: str | None,
    dbt_project_dir: str | None,
    dbt_target_path: str | None,
    log_level: str | None,
    log_file: str | None,
    state_file: str | None,
) -> None:
    """Run a command with automatic Slack notifications.

    \b
    Examples:
        dbt-slack-notify dbt run --selector incremental
        dbt-slack-notify --type dbt-test --label Elementary dbt test --selector elementary
    """
    settings = Settings()

    _configure_logging(
        log_level if log_level is not None else settings.log_level,
        log_file=log_file if log_file is not None else settings.log_file,
    )

    runner = SlackNotifyingRunner(
        state_file=Path(state_file if state_file is not None else settings.state_file),
        thread_ts=slack_thread_ts,
        slack_token=slack_token if slack_token is not None else settings.slack_token,
        slack_channel=slack_channel if slack_channel is not None else settings.slack_channel,
        dbt_project_dir=dbt_project_dir if dbt_project_dir is not None else settings.dbt_project_dir,
        dbt_target_path=dbt_target_path if dbt_target_path is not None else settings.dbt_target_path,
    )
    exit_code = runner.run(list(command), notification_type, label=label)
    sys.exit(exit_code)
