"""Tests for dbt_slack_notify.runner."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from helpers import SAMPLE_RUN_RESULTS, write_run_results

from dbt_slack_notify.runner import SlackNotifyingRunner, build_ls_command, detect_notification_type, get_selected_models


class TestDetectNotificationType:
    def test_dbt_run(self) -> None:
        assert detect_notification_type(["dbt", "run", "--selector", "inc"]) == "dbt-run"

    def test_dbt_test(self) -> None:
        assert detect_notification_type(["dbt", "test"]) == "dbt-test"

    def test_dbt_seed(self) -> None:
        assert detect_notification_type(["dbt", "seed"]) == "dbt-seed"

    def test_dbt_with_flags(self) -> None:
        assert detect_notification_type(["dbt", "--debug", "run"]) == "dbt-run"

    def test_unknown(self) -> None:
        assert detect_notification_type(["dbt", "run-operation", "foo"]) is None

    def test_no_dbt(self) -> None:
        assert detect_notification_type(["python", "script.py"]) is None


class TestBuildLsCommand:
    def test_basic(self) -> None:
        result = build_ls_command(["dbt", "run", "--selector", "inc"])
        assert result is not None
        assert "ls" in result
        assert "run" not in result
        assert "--resource-type" in result
        assert "--exclude" in result
        exclude_idx = result.index("--exclude")
        assert result[exclude_idx + 1] == "config.materialized:ephemeral"

    def test_strips_run_only_flags(self) -> None:
        result = build_ls_command(["dbt", "run", "--full-refresh", "--selector", "inc"])
        assert result is not None
        assert "--full-refresh" not in result

    def test_no_dbt_run(self) -> None:
        assert build_ls_command(["dbt", "test"]) is None

    def test_preserves_other_args(self) -> None:
        result = build_ls_command(["with-role", "dbt", "run", "--selector", "inc"])
        assert result is not None
        assert "with-role" in result
        assert "--selector" in result


class TestGetSelectedModels:
    @patch("dbt_slack_notify.runner.subprocess.run")
    def test_returns_model_list(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="model_a\nmodel_b\nmodel_c\n", stderr="")
        result = get_selected_models(["dbt", "run", "--selector", "inc"])
        assert result == ["model_a", "model_b", "model_c"]

    @patch("dbt_slack_notify.runner.subprocess.run")
    def test_empty_output(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = get_selected_models(["dbt", "run"])
        assert result == []

    @patch("dbt_slack_notify.runner.subprocess.run")
    def test_nonzero_exit_code(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
        result = get_selected_models(["dbt", "run"])
        assert result is None

    @patch("dbt_slack_notify.runner.subprocess.run")
    def test_timeout_exception(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="dbt ls", timeout=120)
        result = get_selected_models(["dbt", "run"])
        assert result is None

    def test_non_run_command_returns_none(self) -> None:
        result = get_selected_models(["dbt", "test"])
        assert result is None


class TestSlackNotifyingRunner:
    @patch("dbt_slack_notify.runner.get_slack_client")
    def test_run_success(
        self, mock_get_client: MagicMock,
        tmp_path: Path, run_results_path: Path,
    ) -> None:
        client = MagicMock()
        client.chat_postMessage.return_value = {"ts": "123"}
        mock_get_client.return_value = client

        write_run_results(run_results_path, SAMPLE_RUN_RESULTS)

        state_file = tmp_path / "state.json"
        runner = SlackNotifyingRunner(
            state_file=state_file, slack_channel="#test",
            dbt_project_dir=str(tmp_path), dbt_target_path=".",
        )
        target = tmp_path / "run_results.json"
        if not target.exists():
            run_results_path.rename(target)

        exit_code = runner.run([sys.executable, "-c", "print('ok')"], notification_type="dbt-run")
        assert exit_code == 0
        assert client.chat_postMessage.call_count >= 2

    @patch("dbt_slack_notify.runner.get_slack_client")
    def test_run_without_slack(
        self, mock_get_client: MagicMock, tmp_path: Path,
    ) -> None:
        mock_get_client.return_value = None

        state_file = tmp_path / "state.json"
        runner = SlackNotifyingRunner(state_file=state_file)
        exit_code = runner.run([sys.executable, "-c", "print('ok')"], notification_type="auto")
        assert exit_code == 0

    @patch("dbt_slack_notify.runner.get_slack_client")
    def test_run_command_failure(
        self, mock_get_client: MagicMock, tmp_path: Path,
    ) -> None:
        mock_get_client.return_value = None

        state_file = tmp_path / "state.json"
        runner = SlackNotifyingRunner(state_file=state_file)
        exit_code = runner.run([sys.executable, "-c", "raise SystemExit(2)"])
        assert exit_code == 2
        state = json.loads(state_file.read_text())
        assert "command_error" in state

    @patch("dbt_slack_notify.runner.get_slack_client")
    def test_thread_ts_stored(
        self, mock_get_client: MagicMock, tmp_path: Path,
    ) -> None:
        mock_get_client.return_value = None

        state_file = tmp_path / "state.json"
        SlackNotifyingRunner(state_file=state_file, thread_ts="ts.123")
        state = json.loads(state_file.read_text())
        assert state["thread_ts"] == "ts.123"

    @patch("dbt_slack_notify.runner.get_slack_client")
    def test_cli_options_passed_through(
        self, mock_get_client: MagicMock, tmp_path: Path,
    ) -> None:
        mock_get_client.return_value = None

        state_file = tmp_path / "state.json"
        runner = SlackNotifyingRunner(
            state_file=state_file, slack_token="tok", slack_channel="#ch",
            dbt_project_dir="/proj", dbt_target_path="out",
        )
        mock_get_client.assert_called_once_with(token="tok")
        assert runner.channel == "#ch"
        assert runner.dbt_project_dir == "/proj"
        assert runner.dbt_target_path == "out"
