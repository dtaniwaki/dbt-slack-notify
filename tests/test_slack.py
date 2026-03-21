"""Tests for dbt_slack_notify.slack."""

from dbt_slack_notify.slack import get_slack_client


class TestGetSlackClient:
    def test_no_token(self) -> None:
        assert get_slack_client() is None

    def test_with_token(self) -> None:
        client = get_slack_client(token="xoxb-fake")
        assert client is not None
