"""Tests for dbt_slack_notify.cli."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from dbt_slack_notify.cli import cli


class TestCli:
    def test_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "--type" in result.output
        assert "dbt-run" in result.output
        assert "--log-level" in result.output

    def test_invalid_type(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--type", "invalid", "echo", "hi"])
        assert result.exit_code != 0

    def test_invalid_log_level(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--log-level", "INVALID", "echo", "hi"])
        assert result.exit_code != 0


class TestCliSettingsIntegration:
    @patch("dbt_slack_notify.cli.SlackNotifyingRunner")
    def test_env_var_resolved_via_settings(
        self, mock_runner_cls: pytest.fixture, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("DBT_SLACK_NOTIFY_SLACK_TOKEN", "xoxb-env")
        monkeypatch.setenv("DBT_SLACK_NOTIFY_SLACK_CHANNEL", "#env-ch")
        mock_runner = mock_runner_cls.return_value
        mock_runner.run.return_value = 0

        runner = CliRunner()
        result = runner.invoke(cli, ["echo", "hi"])
        assert result.exit_code == 0
        call_kwargs = mock_runner_cls.call_args[1]
        assert call_kwargs["slack_token"] == "xoxb-env"
        assert call_kwargs["slack_channel"] == "#env-ch"

    @patch("dbt_slack_notify.cli.SlackNotifyingRunner")
    def test_cli_option_overrides_settings(
        self, mock_runner_cls: pytest.fixture, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("DBT_SLACK_NOTIFY_SLACK_TOKEN", "xoxb-env")
        monkeypatch.setenv("DBT_SLACK_NOTIFY_SLACK_CHANNEL", "#env-ch")
        mock_runner = mock_runner_cls.return_value
        mock_runner.run.return_value = 0

        runner = CliRunner()
        result = runner.invoke(cli, [
            "--slack-token", "xoxb-cli",
            "--slack-channel", "#cli-ch",
            "echo", "hi",
        ])
        assert result.exit_code == 0
        call_kwargs = mock_runner_cls.call_args[1]
        assert call_kwargs["slack_token"] == "xoxb-cli"
        assert call_kwargs["slack_channel"] == "#cli-ch"

    @patch("dbt_slack_notify.cli.SlackNotifyingRunner")
    def test_state_file_option(self, mock_runner_cls: pytest.fixture) -> None:
        mock_runner = mock_runner_cls.return_value
        mock_runner.run.return_value = 0

        runner = CliRunner()
        result = runner.invoke(cli, ["--state-file", "/tmp/custom.json", "echo", "hi"])
        assert result.exit_code == 0
        call_kwargs = mock_runner_cls.call_args[1]
        assert call_kwargs["state_file"] == Path("/tmp/custom.json")

    @patch("dbt_slack_notify.cli.SlackNotifyingRunner")
    def test_log_file_option(self, mock_runner_cls: pytest.fixture, tmp_path: Path) -> None:
        mock_runner = mock_runner_cls.return_value
        mock_runner.run.return_value = 0

        log_file = str(tmp_path / "test.log")
        runner = CliRunner()
        result = runner.invoke(cli, ["--log-file", log_file, "echo", "hi"])
        assert result.exit_code == 0

    @patch("dbt_slack_notify.cli.SlackNotifyingRunner")
    def test_default_state_file_uses_tempdir(self, mock_runner_cls: pytest.fixture) -> None:
        mock_runner = mock_runner_cls.return_value
        mock_runner.run.return_value = 0

        runner = CliRunner()
        result = runner.invoke(cli, ["echo", "hi"])
        assert result.exit_code == 0
        call_kwargs = mock_runner_cls.call_args[1]
        expected_dir = tempfile.gettempdir()
        assert str(call_kwargs["state_file"]).startswith(expected_dir)


class TestCliTimeout:
    @patch("dbt_slack_notify.cli.SlackNotifyingRunner")
    def test_timeout_parsed_to_seconds(self, mock_runner_cls: pytest.fixture) -> None:
        mock_runner = mock_runner_cls.return_value
        mock_runner.run.return_value = 0

        runner = CliRunner()
        result = runner.invoke(cli, ["--timeout", "240m", "--kill-grace", "5m", "echo", "hi"])
        assert result.exit_code == 0
        run_kwargs = mock_runner.run.call_args[1]
        assert run_kwargs["timeout"] == 14400
        assert run_kwargs["kill_grace"] == 300

    @patch("dbt_slack_notify.cli.SlackNotifyingRunner")
    def test_default_timeout_is_none(self, mock_runner_cls: pytest.fixture) -> None:
        mock_runner = mock_runner_cls.return_value
        mock_runner.run.return_value = 0

        runner = CliRunner()
        result = runner.invoke(cli, ["echo", "hi"])
        assert result.exit_code == 0
        run_kwargs = mock_runner.run.call_args[1]
        assert run_kwargs["timeout"] is None
        assert run_kwargs["kill_grace"] == 300

    def test_invalid_timeout(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--timeout", "abc", "echo", "hi"])
        assert result.exit_code != 0


class TestCliProgress:
    @patch("dbt_slack_notify.cli.SlackNotifyingRunner")
    def test_progress_options_passed_through(self, mock_runner_cls: pytest.fixture) -> None:
        mock_runner = mock_runner_cls.return_value
        mock_runner.run.return_value = 0

        runner = CliRunner()
        result = runner.invoke(cli, [
            "--progress-step", "10",
            "--progress-min-nodes", "5",
            "--progress-min-interval", "2m",
            "echo", "hi",
        ])
        assert result.exit_code == 0
        run_kwargs = mock_runner.run.call_args[1]
        assert run_kwargs["progress_step"] == 10
        assert run_kwargs["progress_min_nodes"] == 5
        assert run_kwargs["progress_min_interval"] == 120

    @patch("dbt_slack_notify.cli.SlackNotifyingRunner")
    def test_progress_defaults_none(self, mock_runner_cls: pytest.fixture) -> None:
        mock_runner = mock_runner_cls.return_value
        mock_runner.run.return_value = 0

        runner = CliRunner()
        result = runner.invoke(cli, ["echo", "hi"])
        assert result.exit_code == 0
        run_kwargs = mock_runner.run.call_args[1]
        assert run_kwargs["progress_step"] is None
        assert run_kwargs["progress_min_nodes"] is None
        assert run_kwargs["progress_min_interval"] is None

    @patch("dbt_slack_notify.cli.SlackNotifyingRunner")
    def test_progress_step_defaults_min_interval(
        self, mock_runner_cls: pytest.fixture,
    ) -> None:
        mock_runner = mock_runner_cls.return_value
        mock_runner.run.return_value = 0

        runner = CliRunner()
        result = runner.invoke(cli, ["--progress-step", "10", "echo", "hi"])
        assert result.exit_code == 0
        run_kwargs = mock_runner.run.call_args[1]
        assert run_kwargs["progress_min_interval"] == 300

    @patch("dbt_slack_notify.cli.SlackNotifyingRunner")
    def test_progress_step_from_env(
        self, mock_runner_cls: pytest.fixture, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("DBT_SLACK_NOTIFY_PROGRESS_STEP", "20")
        mock_runner = mock_runner_cls.return_value
        mock_runner.run.return_value = 0

        runner = CliRunner()
        result = runner.invoke(cli, ["echo", "hi"])
        assert result.exit_code == 0
        run_kwargs = mock_runner.run.call_args[1]
        assert run_kwargs["progress_step"] == 20

    def test_progress_step_out_of_range(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--progress-step", "0", "echo", "hi"])
        assert result.exit_code != 0
        result = runner.invoke(cli, ["--progress-step", "101", "echo", "hi"])
        assert result.exit_code != 0

    def test_progress_min_nodes_non_positive(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--progress-min-nodes", "0", "echo", "hi"])
        assert result.exit_code != 0

    def test_invalid_progress_min_interval(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--progress-min-interval", "abc", "echo", "hi"])
        assert result.exit_code != 0
