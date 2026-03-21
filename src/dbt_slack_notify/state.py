"""Build state persistence (single JSON file, read-modify-write)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, cast

logger = logging.getLogger(__name__)


def load_state(state_file: Path) -> dict[str, Any]:
    """Load build state from JSON file. Returns empty dict if missing or invalid."""
    if not state_file.exists():
        return {}
    try:
        return cast(dict[str, Any], json.loads(state_file.read_text()))
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load state file %s: %s", state_file, e)
        return {}


def update_state(updates: dict[str, Any], state_file: Path) -> None:
    """Merge *updates* into the existing state file (read-modify-write)."""
    state = load_state(state_file)
    state.update(updates)
    try:
        state_file.write_text(json.dumps(state, indent=2))
    except OSError as e:
        logger.error("Failed to write state file %s: %s", state_file, e)
