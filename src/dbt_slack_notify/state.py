"""Build state persistence (single JSON file, read-modify-write with flock)."""

from __future__ import annotations

import fcntl
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
    """Merge *updates* into the existing state file (read-modify-write with exclusive lock)."""
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        mode = "r+" if state_file.exists() else "w"
        with open(state_file, mode) as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                if mode == "r+":
                    raw = f.read()
                    state: dict[str, Any] = json.loads(raw) if raw.strip() else {}
                else:
                    state = {}
                state.update(updates)
                f.seek(0)
                f.write(json.dumps(state, indent=2))
                f.truncate()
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except OSError as e:
        logger.error("Failed to write state file %s: %s", state_file, e)
