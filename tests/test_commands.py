"""Tests for dbt_slack_notify.commands."""

import json
from pathlib import Path
from unittest.mock import MagicMock

from helpers import SAMPLE_RUN_RESULTS, SAMPLE_TEST_RESULTS, write_run_results

from dbt_slack_notify.commands import (
    cmd_dbt_run,
    cmd_dbt_seed,
    cmd_dbt_test,
    cmd_message,
)
from dbt_slack_notify.state import load_state


class TestCmdMessage:
    def test_posts_message(self, mock_slack_client: MagicMock, tmp_state_file: Path) -> None:
        cmd_message(mock_slack_client, "#test", tmp_state_file, "hello")
        call_kwargs = mock_slack_client.chat_postMessage.call_args[1]
        assert call_kwargs["text"] == "hello"

    def test_uses_thread_ts(self, mock_slack_client: MagicMock, tmp_state_file: Path) -> None:
        tmp_state_file.write_text(json.dumps({"thread_ts": "ts123"}))
        cmd_message(mock_slack_client, "#test", tmp_state_file, "msg")
        call_kwargs = mock_slack_client.chat_postMessage.call_args[1]
        assert call_kwargs["thread_ts"] == "ts123"


class TestCmdDbtSeed:
    def test_posts_stats(
        self, mock_slack_client: MagicMock, tmp_state_file: Path, run_results_path: Path,
    ) -> None:
        data = {
            "elapsed_time": 5.0,
            "results": [{"unique_id": "seed.project.raw_users", "status": "success"}],
        }
        write_run_results(run_results_path, data)
        cmd_dbt_seed(mock_slack_client, "#test", tmp_state_file, run_results_path)
        mock_slack_client.chat_postMessage.assert_called_once()
        state = load_state(tmp_state_file)
        assert "seed_stats" in state

    def test_skips_when_no_seed_results(
        self, mock_slack_client: MagicMock, tmp_state_file: Path, run_results_path: Path,
    ) -> None:
        data = {
            "elapsed_time": 5.0,
            "results": [{"unique_id": "model.project.users", "status": "success"}],
        }
        write_run_results(run_results_path, data)
        cmd_dbt_seed(mock_slack_client, "#test", tmp_state_file, run_results_path)
        mock_slack_client.chat_postMessage.assert_not_called()


class TestCmdDbtRun:
    def test_posts_stats(
        self, mock_slack_client: MagicMock, tmp_state_file: Path, run_results_path: Path,
    ) -> None:
        write_run_results(run_results_path, SAMPLE_RUN_RESULTS)
        cmd_dbt_run(mock_slack_client, "#test", tmp_state_file, run_results_path)
        mock_slack_client.chat_postMessage.assert_called_once()
        state = load_state(tmp_state_file)
        assert "run_stats" in state


class TestCmdDbtTest:
    def test_posts_stats(
        self, mock_slack_client: MagicMock, tmp_state_file: Path, run_results_path: Path,
    ) -> None:
        write_run_results(run_results_path, SAMPLE_TEST_RESULTS)
        cmd_dbt_test(mock_slack_client, "#test", tmp_state_file, run_results_path)
        mock_slack_client.chat_postMessage.assert_called_once()
