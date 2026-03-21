"""Tests for dbt_slack_notify.cli."""

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
