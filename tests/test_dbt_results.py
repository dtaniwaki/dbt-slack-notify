"""Tests for dbt_slack_notify.dbt_results."""

from pathlib import Path

from helpers import SAMPLE_RUN_RESULTS, write_run_results

from dbt_slack_notify.dbt_results import parse_run_results, resolve_results_path


class TestParseRunResults:
    def test_success(self, run_results_path: Path) -> None:
        write_run_results(run_results_path, SAMPLE_RUN_RESULTS)
        counts, elapsed, errors, bytes_scanned, parse_error = parse_run_results(run_results_path)
        assert parse_error is None
        assert counts["model"]["success"] == 1
        assert counts["model"]["error"] == 1
        assert elapsed == 42.5
        assert len(errors) == 1
        assert errors[0].node_name == "broken"
        assert bytes_scanned == 1024

    def test_missing_file(self, tmp_path: Path) -> None:
        missing = tmp_path / "missing.json"
        counts, elapsed, errors, bytes_scanned, parse_error = parse_run_results(missing)
        assert parse_error is not None
        assert "not found" in parse_error.lower()
        assert counts == {}

    def test_invalid_json(self, run_results_path: Path) -> None:
        run_results_path.write_text("{invalid")
        counts, elapsed, errors, bytes_scanned, parse_error = parse_run_results(run_results_path)
        assert parse_error is not None
        assert counts == {}

    def test_empty_results(self, run_results_path: Path) -> None:
        write_run_results(run_results_path, {"results": [], "elapsed_time": 0.0})
        counts, elapsed, errors, bytes_scanned, parse_error = parse_run_results(run_results_path)
        assert parse_error is None
        assert counts == {}
        assert elapsed == 0.0


class TestResolveResultsPath:
    def test_explicit(self) -> None:
        result = resolve_results_path("/custom", "out")
        assert result == Path("/custom/out/run_results.json")

    def test_default(self) -> None:
        result = resolve_results_path(".", "target")
        assert result == Path("./target/run_results.json")
