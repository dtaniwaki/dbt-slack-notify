"""Constants for dbt-slack-notify."""

from __future__ import annotations

import logging
from typing import NamedTuple

MAX_ERROR_DETAILS = 5
MAX_ERROR_MSG_LEN = 300


class ErrorEntry(NamedTuple):
    node_name: str
    message: str
    status: str = "error"

STATUS_ORDER: list[str] = ["runtime error", "error", "fail", "warn", "skip", "skipped", "success", "pass"]

EXECUTION_ERROR_STATUSES: frozenset[str] = frozenset({"error", "runtime error"})

TEST_FAILURE_STATUS = "fail"

ERROR_STATUSES: frozenset[str] = EXECUTION_ERROR_STATUSES | {TEST_FAILURE_STATUS}

LOG_LEVELS: dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}
