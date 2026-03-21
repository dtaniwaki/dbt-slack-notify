"""Test helper utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_run_results(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data))


SAMPLE_RUN_RESULTS: dict[str, Any] = {
    "elapsed_time": 42.5,
    "results": [
        {
            "unique_id": "model.project.users",
            "status": "success",
            "adapter_response": {"data_scanned_in_bytes": 1024},
        },
        {
            "unique_id": "model.project.broken",
            "status": "error",
            "message": "Something went wrong",
            "adapter_response": {},
        },
    ],
}

SAMPLE_TEST_RESULTS: dict[str, Any] = {
    "elapsed_time": 15.0,
    "results": [
        {"unique_id": "test.project.not_null_id", "status": "pass"},
        {"unique_id": "test.project.unique_id", "status": "pass"},
        {"unique_id": "test.project.ref_integrity", "status": "fail", "message": "referential integrity failed"},
    ],
}
