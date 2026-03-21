"""Slack Block Kit builders."""

from __future__ import annotations

from typing import Any

from dbt_slack_notify.constants import MAX_ERROR_DETAILS, MAX_ERROR_MSG_LEN, ErrorEntry
from dbt_slack_notify.formatters import format_duration, format_stats_table


def build_error_details_blocks(
    errors: list[ErrorEntry],
    max_errors: int = MAX_ERROR_DETAILS,
) -> list[dict[str, Any]]:
    """Build Slack Block Kit blocks for error details."""
    if not errors:
        return []

    shown = errors[:max_errors]
    lines: list[str] = []
    for node_name, message in shown:
        truncated = message[:MAX_ERROR_MSG_LEN] + "..." if len(message) > MAX_ERROR_MSG_LEN else message
        safe_message = truncated.replace("```", "'''")
        lines.append(f"\u274c *{node_name}*\n```{safe_message}```")
    text = "\n".join(lines)
    if len(errors) > max_errors:
        remaining = len(errors) - max_errors
        text += f"\n_\uff08\u4ed6 {remaining} \u4ef6\u306e\u30a8\u30e9\u30fc\u304c\u3042\u308a\u307e\u3059\uff09_"
    return [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]


def build_stats_blocks(
    counts: dict[str, dict[str, int]],
    resource_types: list[str],
    elapsed_time: float,
    title: str = "",
    errors: list[ErrorEntry] | None = None,
) -> list[dict[str, Any]]:
    """Build Slack Block Kit blocks for dbt run/test stats."""
    table = format_stats_table(counts, resource_types)
    duration = f" ({format_duration(elapsed_time)})" if elapsed_time > 0 else ""
    prefix = f"*{title}{duration}*\n" if title else ""
    stats_text = f"{prefix}```{table}```"
    blocks: list[dict[str, Any]] = [
        {"type": "section", "text": {"type": "mrkdwn", "text": stats_text}},
    ]
    if errors:
        blocks.extend(build_error_details_blocks(errors))
    return blocks
