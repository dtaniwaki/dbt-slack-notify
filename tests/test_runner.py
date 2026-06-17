"""Tests for dbt_slack_notify.runner."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from helpers import SAMPLE_RUN_RESULTS, write_run_results

from dbt_slack_notify.runner import (
    SlackNotifyingRunner,
    build_ls_command,
    build_ls_command_for_build,
    detect_notification_type,
    get_selected_models,
    get_selected_nodes,
    get_selected_nodes_by_resource_type,
)


class TestDetectNotificationType:
    def test_dbt_run(self) -> None:
        assert detect_notification_type(["dbt", "run", "--selector", "inc"]) == "dbt-run"

    def test_dbt_test(self) -> None:
        assert detect_notification_type(["dbt", "test"]) == "dbt-test"

    def test_dbt_seed(self) -> None:
        assert detect_notification_type(["dbt", "seed"]) == "dbt-seed"

    def test_dbt_build(self) -> None:
        assert detect_notification_type(["dbt", "build", "--selector", "inc"]) == "dbt-build"

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

    def test_dbt_build(self) -> None:
        result = build_ls_command(["dbt", "build", "--selector", "inc"])
        assert result is not None
        assert "ls" in result
        assert "build" not in result
        assert "--selector" in result

    def test_resource_type_override(self) -> None:
        result = build_ls_command(["dbt", "build"], resource_type="seed", exclude_ephemeral=False)
        assert result is not None
        rt_idx = result.index("--resource-type")
        assert result[rt_idx + 1] == "seed"
        assert "--exclude" not in result

    def test_resource_type_test_no_ephemeral_exclude(self) -> None:
        result = build_ls_command(["dbt", "build"], resource_type="test", exclude_ephemeral=False)
        assert result is not None
        assert "test" in result[result.index("--resource-type") + 1:result.index("--resource-type") + 2]
        assert "--exclude" not in result

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


class TestGetSelectedNodes:
    @patch("dbt_slack_notify.runner.subprocess.run")
    def test_seed_resource_type(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="seed_a\nseed_b\n", stderr="")
        result = get_selected_nodes(["dbt", "build"], resource_type="seed", exclude_ephemeral=False)
        assert result == ["seed_a", "seed_b"]
        args = mock_run.call_args[0][0]
        assert args[args.index("--resource-type") + 1] == "seed"
        assert "--exclude" not in args

    @patch("dbt_slack_notify.runner.subprocess.run")
    def test_test_resource_type(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=0, stdout="test_a\n", stderr="")
        result = get_selected_nodes(["dbt", "build"], resource_type="test", exclude_ephemeral=False)
        assert result == ["test_a"]


class TestBuildLsCommandForBuild:
    def test_basic(self) -> None:
        result = build_ls_command_for_build(["dbt", "build", "--selector", "inc"])
        assert result is not None
        assert "ls" in result
        assert "build" not in result
        rt_args = [result[i + 1] for i, a in enumerate(result) if a == "--resource-type"]
        assert rt_args == ["seed", "model", "test"]
        assert "--output" in result
        assert result[result.index("--output") + 1] == "json"
        exclude_idx = result.index("--exclude")
        assert result[exclude_idx + 1] == "config.materialized:ephemeral"
        assert "--selector" in result

    def test_strips_run_only_flags(self) -> None:
        result = build_ls_command_for_build(["dbt", "build", "--full-refresh"])
        assert result is not None
        assert "--full-refresh" not in result

    def test_non_build_returns_none(self) -> None:
        assert build_ls_command_for_build(["dbt", "run"]) is None
        assert build_ls_command_for_build(["dbt", "test"]) is None


class TestGetSelectedNodesByResourceType:
    @patch("dbt_slack_notify.runner.subprocess.run")
    def test_groups_by_resource_type(self, mock_run: MagicMock) -> None:
        stdout = "\n".join([
            json.dumps({"unique_id": "seed.pkg.seed_a", "resource_type": "seed"}),
            json.dumps({"unique_id": "model.pkg.model_a", "resource_type": "model"}),
            json.dumps({"unique_id": "model.pkg.model_b", "resource_type": "model"}),
            json.dumps({"unique_id": "test.pkg.test_a", "resource_type": "test"}),
        ])
        mock_run.return_value = MagicMock(returncode=0, stdout=stdout, stderr="")
        result = get_selected_nodes_by_resource_type(["dbt", "build", "--selector", "inc"])
        assert result == {
            "seed": ["seed.pkg.seed_a"],
            "model": ["model.pkg.model_a", "model.pkg.model_b"],
            "test": ["test.pkg.test_a"],
        }
        # Single subprocess call covers all three resource types.
        assert mock_run.call_count == 1

    @patch("dbt_slack_notify.runner.subprocess.run")
    def test_skips_malformed_lines(self, mock_run: MagicMock) -> None:
        stdout = "\n".join([
            "not json",
            json.dumps({"unique_id": "model.pkg.model_a", "resource_type": "model"}),
        ])
        mock_run.return_value = MagicMock(returncode=0, stdout=stdout, stderr="")
        result = get_selected_nodes_by_resource_type(["dbt", "build"])
        assert result == {"seed": [], "model": ["model.pkg.model_a"], "test": []}

    @patch("dbt_slack_notify.runner.subprocess.run")
    def test_nonzero_exit_code(self, mock_run: MagicMock) -> None:
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="boom")
        assert get_selected_nodes_by_resource_type(["dbt", "build"]) is None

    @patch("dbt_slack_notify.runner.subprocess.run")
    def test_timeout_exception(self, mock_run: MagicMock) -> None:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="dbt ls", timeout=120)
        assert get_selected_nodes_by_resource_type(["dbt", "build"]) is None

    def test_non_build_returns_none(self) -> None:
        assert get_selected_nodes_by_resource_type(["dbt", "run"]) is None


class TestNotifyStartBuild:
    @patch("dbt_slack_notify.runner.get_slack_client")
    @patch("dbt_slack_notify.runner.get_selected_nodes_by_resource_type")
    def test_posts_three_messages(
        self, mock_get_grouped: MagicMock, mock_get_client: MagicMock, tmp_path: Path,
    ) -> None:
        client = MagicMock()
        client.chat_postMessage.return_value = {"ts": "100"}
        mock_get_client.return_value = client
        mock_get_grouped.return_value = {
            "seed": ["seed_a", "seed_b"],
            "model": ["model_a", "model_b", "model_c"],
            "test": ["test_a"],
        }

        state_file = tmp_path / "state.json"
        runner = SlackNotifyingRunner(state_file=state_file, slack_channel="#test")
        runner._notify_start("dbt-build", ["dbt", "build", "--selector", "daily"], label=None)

        messages = [c.kwargs.get("text", "") for c in client.chat_postMessage.call_args_list]
        assert any("dbt build (seed) 開始（2件）" in m for m in messages)
        assert any("dbt build (model) 開始（3件）" in m for m in messages)
        assert any("dbt build (test) 開始（1件）" in m for m in messages)
        assert client.files_upload_v2.call_count == 3
        filenames = {c.kwargs["filename"] for c in client.files_upload_v2.call_args_list}
        assert filenames == {"seeds_to_build.txt", "models_to_build.txt", "tests_to_build.txt"}
        # Grouping function is invoked once, not once per category.
        assert mock_get_grouped.call_count == 1

    @patch("dbt_slack_notify.runner.get_slack_client")
    @patch("dbt_slack_notify.runner.get_selected_nodes_by_resource_type")
    def test_skips_empty_categories(
        self, mock_get_grouped: MagicMock, mock_get_client: MagicMock, tmp_path: Path,
    ) -> None:
        client = MagicMock()
        client.chat_postMessage.return_value = {"ts": "100"}
        mock_get_client.return_value = client
        mock_get_grouped.return_value = {
            "seed": [],
            "model": ["model_a"],
            "test": [],
        }

        state_file = tmp_path / "state.json"
        runner = SlackNotifyingRunner(state_file=state_file, slack_channel="#test")
        runner._notify_start("dbt-build", ["dbt", "build"], label=None)

        messages = [c.kwargs.get("text", "") for c in client.chat_postMessage.call_args_list]
        assert len(messages) == 1
        assert "dbt build (model) 開始（1件）" in messages[0]
        assert client.files_upload_v2.call_count == 1

    @patch("dbt_slack_notify.runner.get_slack_client")
    @patch("dbt_slack_notify.runner.get_selected_nodes_by_resource_type")
    def test_fallback_when_ls_failed(
        self, mock_get_grouped: MagicMock, mock_get_client: MagicMock, tmp_path: Path,
    ) -> None:
        client = MagicMock()
        client.chat_postMessage.return_value = {"ts": "100"}
        mock_get_client.return_value = client
        mock_get_grouped.return_value = None

        state_file = tmp_path / "state.json"
        runner = SlackNotifyingRunner(state_file=state_file, slack_channel="#test")
        runner._notify_start("dbt-build", ["dbt", "build"], label="Daily")

        messages = [c.kwargs.get("text", "") for c in client.chat_postMessage.call_args_list]
        assert len(messages) == 1
        assert "dbt build 開始 (Daily)" in messages[0]
        client.files_upload_v2.assert_not_called()

    @patch("dbt_slack_notify.runner.get_slack_client")
    @patch("dbt_slack_notify.runner.get_selected_nodes_by_resource_type")
    def test_fallback_when_all_categories_empty(
        self, mock_get_grouped: MagicMock, mock_get_client: MagicMock, tmp_path: Path,
    ) -> None:
        client = MagicMock()
        client.chat_postMessage.return_value = {"ts": "100"}
        mock_get_client.return_value = client
        mock_get_grouped.return_value = {"seed": [], "model": [], "test": []}

        state_file = tmp_path / "state.json"
        runner = SlackNotifyingRunner(state_file=state_file, slack_channel="#test")
        runner._notify_start("dbt-build", ["dbt", "build"], label=None)

        messages = [c.kwargs.get("text", "") for c in client.chat_postMessage.call_args_list]
        assert len(messages) == 1
        assert "dbt build 開始" in messages[0]
        client.files_upload_v2.assert_not_called()


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
    def test_run_timeout_sends_timeout_notification(
        self, mock_get_client: MagicMock, tmp_path: Path,
    ) -> None:
        client = MagicMock()
        client.chat_postMessage.return_value = {"ts": "123"}
        mock_get_client.return_value = client

        state_file = tmp_path / "state.json"
        runner = SlackNotifyingRunner(state_file=state_file, slack_channel="#test")
        exit_code = runner.run(
            [sys.executable, "-c", "raise SystemExit(124)"],
            notification_type="dbt-run",
        )
        assert exit_code == 124
        messages = [
            call.kwargs.get("text", "") or call.args[0] if call.args else call.kwargs.get("text", "")
            for call in client.chat_postMessage.call_args_list
        ]
        timeout_messages = [m for m in messages if "タイムアウト" in m]
        assert len(timeout_messages) == 1

    @patch("dbt_slack_notify.runner.get_slack_client")
    def test_run_timeout_unknown_command(
        self, mock_get_client: MagicMock, tmp_path: Path,
    ) -> None:
        client = MagicMock()
        client.chat_postMessage.return_value = {"ts": "123"}
        mock_get_client.return_value = client

        state_file = tmp_path / "state.json"
        runner = SlackNotifyingRunner(state_file=state_file, slack_channel="#test")
        exit_code = runner.run(
            [sys.executable, "-c", "raise SystemExit(124)"],
            notification_type="auto",
        )
        assert exit_code == 124
        messages = [
            call.kwargs.get("text", "") or call.args[0] if call.args else call.kwargs.get("text", "")
            for call in client.chat_postMessage.call_args_list
        ]
        timeout_messages = [m for m in messages if "タイムアウト" in m]
        assert len(timeout_messages) == 1

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
