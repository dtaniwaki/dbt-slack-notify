"""Formatting helpers for dbt-slack-notify."""

from __future__ import annotations

from dbt_slack_notify.constants import STATUS_ORDER


def format_duration(seconds: float) -> str:
    """Format seconds as human-readable duration (e.g. '4m 32s')."""
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def format_stats_table(counts: dict[str, dict[str, int]], resource_types: list[str]) -> str:
    """Format stats as a monospace table (for use inside a code block)."""
    present = [rt for rt in resource_types if rt in counts]
    if not present:
        return "no results"

    seen: set[str] = set()
    statuses: list[str] = []
    for s in STATUS_ORDER:
        for rt in present:
            if s in counts[rt] and s not in seen:
                statuses.append(s)
                seen.add(s)
    for rt in present:
        for s in counts[rt]:
            if s not in seen:
                statuses.append(s)
                seen.add(s)

    headers = ["", "total"] + statuses
    rows: list[list[str]] = []
    for rt in present:
        sc = counts[rt]
        total = sum(sc.values())
        rows.append([rt, str(total)] + [str(sc.get(s, "-")) for s in statuses])

    all_rows = [headers] + rows
    widths = [max(len(r[i]) for r in all_rows) for i in range(len(headers))]

    lines = []
    for i, row in enumerate(all_rows):
        lines.append("  ".join(cell.ljust(widths[j]) for j, cell in enumerate(row)).rstrip())
        if i == 0:
            lines.append("  ".join("-" * widths[j] for j in range(len(headers))).rstrip())
    return "\n".join(lines)
