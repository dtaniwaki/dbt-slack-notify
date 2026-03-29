"""Tests for dbt_slack_notify.blocks."""

from dbt_slack_notify.blocks import build_error_details_blocks, build_stats_blocks
from dbt_slack_notify.constants import ErrorEntry


class TestBuildErrorDetailsBlocks:
    def test_empty(self) -> None:
        assert build_error_details_blocks([]) == []

    def test_single_error(self) -> None:
        blocks = build_error_details_blocks([ErrorEntry("node", "msg")])
        assert len(blocks) == 1
        assert "node" in blocks[0]["text"]["text"]  # type: ignore[index]

    def test_truncation(self) -> None:
        long_msg = "x" * 500
        blocks = build_error_details_blocks([ErrorEntry("node", long_msg)])
        text = blocks[0]["text"]["text"]  # type: ignore[index]
        assert "..." in text

    def test_overflow_message(self) -> None:
        errors = [ErrorEntry("node" + str(i), "msg") for i in range(10)]
        blocks = build_error_details_blocks(errors, max_errors=3)
        text = blocks[0]["text"]["text"]  # type: ignore[index]
        assert "7" in text


class TestBuildStatsBlocks:
    def test_basic(self) -> None:
        counts = {"model": {"success": 1}}
        blocks = build_stats_blocks(counts, ["model"], 10.0, title="dbt run")
        assert len(blocks) >= 1
        text = blocks[0]["text"]["text"]  # type: ignore[index]
        assert "dbt run" in text
        assert "10s" in text

    def test_with_bytes_scanned(self) -> None:
        counts = {"model": {"success": 1}}
        blocks = build_stats_blocks(counts, ["model"], 10.0, title="dbt run", bytes_scanned=5 * 1024 * 1024)
        text = blocks[0]["text"]["text"]  # type: ignore[index]
        assert "scanned 5.0 MB" in text
        assert "10s" in text

    def test_bytes_scanned_zero_omitted(self) -> None:
        counts = {"model": {"success": 1}}
        blocks = build_stats_blocks(counts, ["model"], 10.0, title="dbt run", bytes_scanned=0)
        text = blocks[0]["text"]["text"]  # type: ignore[index]
        assert "scanned" not in text

    def test_with_errors(self) -> None:
        counts = {"model": {"error": 1}}
        errors = [ErrorEntry("broken", "fail msg")]
        blocks = build_stats_blocks(counts, ["model"], 5.0, title="dbt run", errors=errors)
        assert len(blocks) == 2
