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
