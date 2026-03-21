"""Tests for dbt_slack_notify.formatters."""

from dbt_slack_notify.formatters import format_duration, format_stats_table


class TestFormatDuration:
    def test_seconds_only(self) -> None:
        assert format_duration(45.0) == "45s"

    def test_minutes_and_seconds(self) -> None:
        assert format_duration(272.0) == "4m 32s"

    def test_hours(self) -> None:
        assert format_duration(3661.0) == "1h 1m 1s"

    def test_zero(self) -> None:
        assert format_duration(0.0) == "0s"


class TestFormatStatsTable:
    def test_basic_table(self) -> None:
        counts = {"model": {"success": 3, "error": 1}}
        result = format_stats_table(counts, ["model"])
        assert "model" in result
        assert "total" in result
        assert "4" in result

    def test_no_results(self) -> None:
        assert format_stats_table({}, ["model"]) == "no results"

    def test_multiple_resource_types(self) -> None:
        counts = {"model": {"success": 2}, "seed": {"success": 1}}
        result = format_stats_table(counts, ["model", "seed"])
        assert "model" in result
        assert "seed" in result
