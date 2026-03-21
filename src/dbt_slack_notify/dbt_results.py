"""dbt run_results.json parser."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from dbt_slack_notify.constants import ERROR_STATUSES, ErrorEntry

logger = logging.getLogger(__name__)


def parse_run_results(
    results_path: Path,
) -> tuple[dict[str, dict[str, int]], float, list[ErrorEntry], int, str | None]:
    """Parse run_results.json and return (counts_by_resource_type, elapsed_time, errors, bytes_scanned, parse_error).

    parse_error is None on success, or an error message string if the file could not be read/parsed.
    """
    counts: dict[str, dict[str, int]] = {}
    elapsed_time = 0.0
    errors: list[ErrorEntry] = []
    bytes_scanned = 0

    if not results_path.exists():
        return counts, elapsed_time, errors, bytes_scanned, f"Run results not found: `{results_path}`"

    try:
        with open(results_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to parse run_results.json: %s", e)
        return counts, elapsed_time, errors, bytes_scanned, f"Failed to parse run results: `{e}`"

    for result in data.get("results", []):
        unique_id = result.get("unique_id", "")
        resource_type = unique_id.split(".")[0] if unique_id else "unknown"
        status = result.get("status", "unknown")
        if resource_type not in counts:
            counts[resource_type] = {}
        counts[resource_type][status] = counts[resource_type].get(status, 0) + 1

        if status in ERROR_STATUSES:
            parts = unique_id.split(".")
            node_name = ".".join(parts[2:]) if len(parts) > 2 else unique_id
            message = result.get("message") or ""
            errors.append(ErrorEntry(node_name, message))

        adapter_response = result.get("adapter_response") or {}
        bytes_scanned += int(adapter_response.get("data_scanned_in_bytes") or 0)

    if "elapsed_time" in data:
        elapsed_time = float(data["elapsed_time"])

    return counts, elapsed_time, errors, bytes_scanned, None


def resolve_results_path(project_dir: str, target_path: str) -> Path:
    """Resolve the run_results.json path."""
    return Path(project_dir) / target_path / "run_results.json"
