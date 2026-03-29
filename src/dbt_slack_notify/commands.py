"""Command functions for each notification sub-command."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from slack_sdk import WebClient

from dbt_slack_notify.blocks import build_stats_blocks
from dbt_slack_notify.constants import ErrorEntry
from dbt_slack_notify.dbt_results import parse_run_results
from dbt_slack_notify.state import load_state, update_state

logger = logging.getLogger(__name__)


def _post_stats(
    client: WebClient,
    channel: str,
    thread_ts: str | None,
    counts: dict[str, dict[str, int]],
    resource_types: list[str],
    elapsed_time: float,
    title: str,
    errors: list[ErrorEntry],
    parse_error: str | None,
    text: str,
    command_error: str | None = None,
    bytes_scanned: int = 0,
) -> None:
    """Post run/test stats (or parse error) to Slack."""
    if parse_error:
        fail_label = "\u7d50\u679c\u306e\u8aad\u307f\u8fbc\u307f\u306b\u5931\u6557\u3057\u307e\u3057\u305f"
        error_text = f"\u274c *{title} - {fail_label}*\n{parse_error}"
        if command_error:
            safe_error = command_error.replace("```", "'''")
            error_text += f"\n```{safe_error}```"
        blocks: list[dict[str, Any]] = [
            {"type": "section", "text": {"type": "mrkdwn", "text": error_text}},
        ]
    else:
        blocks = build_stats_blocks(
            counts, resource_types, elapsed_time, title=title, errors=errors, bytes_scanned=bytes_scanned,
        )

    kwargs: dict[str, Any] = {
        "channel": channel,
        "text": text,
        "blocks": blocks,
    }
    if thread_ts:
        kwargs["thread_ts"] = thread_ts
    client.chat_postMessage(**kwargs)


def cmd_message(client: WebClient, channel: str, state_file: Path, message: str) -> None:
    """Post an arbitrary message to the Slack thread."""
    state = load_state(state_file)
    thread_ts = state.get("thread_ts")
    kwargs: dict[str, Any] = {
        "channel": channel,
        "text": message,
        "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": message}}],
    }
    if thread_ts:
        kwargs["thread_ts"] = thread_ts
    client.chat_postMessage(**kwargs)
    logger.info("Posted message to Slack: %s", message)


def _cmd_dbt_stats(
    client: WebClient,
    channel: str,
    state_file: Path,
    results_path: Path,
    title: str,
    state_key: str,
    resource_types: list[str],
    skip_if_empty: bool = False,
) -> None:
    """Post dbt stats as thread reply (shared implementation for seed/run/test)."""
    state = load_state(state_file)
    thread_ts: str | None = state.get("thread_ts")
    command_error: str | None = state.get("command_error")
    counts, elapsed_time, errors, bytes_scanned, parse_error = parse_run_results(results_path)
    if skip_if_empty and not parse_error and not any(counts.get(rt) for rt in resource_types):
        logger.info("No %s results found, skipping notification", title)
        return
    update_state(
        {state_key: {"counts": counts, "elapsed_time": elapsed_time, "bytes_scanned": bytes_scanned}},
        state_file,
    )
    _post_stats(
        client, channel, thread_ts, counts, resource_types, elapsed_time,
        title, errors, parse_error, f"{title} results",
        command_error=command_error if parse_error else None,
        bytes_scanned=bytes_scanned,
    )
    logger.info("Posted %s stats to Slack", title)


def cmd_dbt_seed(
    client: WebClient, channel: str, state_file: Path, results_path: Path, title: str = "dbt seed",
) -> None:
    """Post dbt seed stats as thread reply. Skips notification if no seeds were executed."""
    _cmd_dbt_stats(client, channel, state_file, results_path, title, "seed_stats", ["seed"], skip_if_empty=True)


def cmd_dbt_run(
    client: WebClient, channel: str, state_file: Path, results_path: Path, title: str = "dbt run",
) -> None:
    """Post dbt run stats as thread reply."""
    _cmd_dbt_stats(client, channel, state_file, results_path, title, "run_stats", ["model", "seed", "snapshot"])


def cmd_dbt_test(
    client: WebClient, channel: str, state_file: Path, results_path: Path, title: str = "dbt test",
) -> None:
    """Post dbt test stats as thread reply."""
    _cmd_dbt_stats(client, channel, state_file, results_path, title, "test_stats", ["test", "unit_test"])
