"""Slack client helpers."""

from __future__ import annotations

import logging

from slack_sdk import WebClient

logger = logging.getLogger(__name__)


def get_slack_client(token: str | None = None) -> WebClient | None:
    """Create a Slack WebClient. Returns None if token is not provided."""
    if not token:
        logger.warning("SLACK_TOKEN is not set. Skipping Slack notification.")
        return None
    return WebClient(token=token, timeout=30)
