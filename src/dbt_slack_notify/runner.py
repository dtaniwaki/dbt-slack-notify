"""SlackNotifyingRunner: wraps command execution with Slack notifications."""

from __future__ import annotations

import collections
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

from slack_sdk import WebClient

from dbt_slack_notify.commands import (
    cmd_dbt_run,
    cmd_dbt_seed,
    cmd_dbt_test,
    cmd_message,
)
from dbt_slack_notify.dbt_results import resolve_results_path
from dbt_slack_notify.slack import get_slack_client
from dbt_slack_notify.state import load_state, update_state

logger = logging.getLogger(__name__)

VALID_TYPES = ["dbt-seed", "dbt-run", "dbt-test", "auto"]

START_MESSAGES: dict[str, str] = {
    "dbt-seed": "dbt seed 開始",
    "dbt-run": "dbt run 開始",
    "dbt-test": "dbt test 開始",
}

_RUN_ONLY_FLAGS = frozenset({"--full-refresh", "--fail-fast", "-x"})


def detect_notification_type(command: list[str]) -> str | None:
    """Detect notification type from command arguments.

    Returns None if the command is not a known dbt run/test type.
    """
    for i, arg in enumerate(command):
        if arg == "dbt":
            for subcommand in command[i + 1:]:
                if subcommand.startswith("-"):
                    continue
                if subcommand == "test":
                    return "dbt-test"
                if subcommand == "run":
                    return "dbt-run"
                if subcommand == "seed":
                    return "dbt-seed"
                break
    return None


def build_ls_command(command: list[str]) -> list[str] | None:
    """Convert a ``dbt run`` command to ``dbt ls --output name --quiet``."""
    ls_command: list[str] = []
    replaced = False
    for i, arg in enumerate(command):
        if arg in _RUN_ONLY_FLAGS:
            continue
        if not replaced and arg == "run":
            if any(c == "dbt" for c in command[:i]):
                ls_command.append("ls")
                replaced = True
                continue
        ls_command.append(arg)
    if not replaced:
        return None
    ls_command.extend([
        "--resource-type", "model",
        "--exclude", "config.materialized:ephemeral",
        "--output", "name",
        "--quiet",
    ])
    return ls_command


def get_selected_models(command: list[str]) -> list[str] | None:
    """Run ``dbt ls`` to preview the models that will be executed."""
    ls_command = build_ls_command(command)
    if not ls_command:
        return None
    try:
        result = subprocess.run(ls_command, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            logger.warning("dbt ls failed (exit %d): %s", result.returncode, result.stderr[:500])
            return None
        models = [line.strip() for line in result.stdout.strip().splitlines() if line.strip()]
        return models
    except Exception as e:
        logger.warning("Failed to get selected models: %s", e)
    return None


class SlackNotifyingRunner:
    """Runs a command while sending Slack notifications before and after execution."""

    def __init__(
        self,
        state_file: Path,
        slack_token: str | None = None,
        slack_channel: str | None = None,
        dbt_project_dir: str = ".",
        dbt_target_path: str = "target",
        thread_ts: str | None = None,
    ) -> None:
        self.client: WebClient | None = get_slack_client(token=slack_token)
        self.channel = slack_channel
        self.state_file = state_file
        self.dbt_project_dir = dbt_project_dir
        self.dbt_target_path = dbt_target_path
        if thread_ts:
            update_state({"thread_ts": thread_ts}, self.state_file)

    def _upload_model_list(self, models: list[str]) -> None:
        if not self.client or not self.channel:
            return
        try:
            state = load_state(self.state_file)
            thread_ts = state.get("thread_ts")
            content = "\n".join(models)
            kwargs: dict[str, Any] = {
                "channels": [self.channel],
                "content": content,
                "filename": "models_to_run.txt",
                "title": f"実行予定モデル一覧（{len(models)}件）",
            }
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            self.client.files_upload_v2(**kwargs)
        except Exception as e:
            logger.warning("Failed to upload model list to Slack: %s", e)

    def _build_label_suffix(self, label: str | None) -> str:
        return f" ({label})" if label else ""

    def _notify_start(self, notification_type: str | None, command: list[str], label: str | None) -> None:
        if not self.client or not self.channel:
            return
        suffix = self._build_label_suffix(label)
        try:
            if notification_type == "dbt-run":
                models = get_selected_models(command)
                if models is None:
                    cmd_message(
                        self.client, self.channel, self.state_file,
                        f"{START_MESSAGES[notification_type]}{suffix}",
                    )
                elif models:
                    cmd_message(
                        self.client, self.channel, self.state_file,
                        f"dbt run 開始（{len(models)}件）{suffix}",
                    )
                    self._upload_model_list(models)
                else:
                    cmd_message(
                        self.client, self.channel, self.state_file,
                        f"dbt run 開始（0件）{suffix}",
                    )
            elif notification_type is not None:
                cmd_message(
                    self.client, self.channel, self.state_file,
                    f"{START_MESSAGES[notification_type]}{suffix}",
                )
            else:
                cmd_message(self.client, self.channel, self.state_file, f"実行中: `{' '.join(command)}`")
        except Exception as e:
            logger.warning("Failed to send Slack start notification: %s", e)

    def _notify_finish(self, notification_type: str | None, command: list[str], label: str | None) -> None:
        if not self.client or not self.channel:
            return
        suffix = self._build_label_suffix(label)
        try:
            results_path = resolve_results_path(self.dbt_project_dir, self.dbt_target_path)
            if notification_type == "dbt-seed":
                cmd_dbt_seed(self.client, self.channel, self.state_file, results_path, title=f"dbt seed{suffix}")
            elif notification_type == "dbt-run":
                cmd_dbt_run(self.client, self.channel, self.state_file, results_path, title=f"dbt run{suffix}")
            elif notification_type == "dbt-test":
                cmd_dbt_test(self.client, self.channel, self.state_file, results_path, title=f"dbt test{suffix}")
            else:
                cmd_message(self.client, self.channel, self.state_file, f"完了: `{' '.join(command)}`")
        except Exception as e:
            logger.warning("Failed to send Slack finish notification: %s", e)

    def run(self, command: list[str], notification_type: str = "auto", label: str | None = None) -> int:
        """Execute command with Slack notifications. Returns the exit code."""
        detected_type = notification_type if notification_type != "auto" else detect_notification_type(command)
        update_state({"command_error": None}, self.state_file)

        self._notify_start(detected_type, command, label)

        exit_code = 0
        tail_lines: collections.deque[str] = collections.deque(maxlen=100)
        try:
            with subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            ) as proc:
                assert proc.stdout is not None
                for line in proc.stdout:
                    sys.stdout.write(line)
                    sys.stdout.flush()
                    tail_lines.append(line)
            if proc.returncode != 0:
                exit_code = proc.returncode
                command_error = "".join(tail_lines)[-2000:]
                update_state({"command_error": command_error}, self.state_file)
        except Exception as e:
            exit_code = 1
            update_state({"command_error": str(e)}, self.state_file)

        self._notify_finish(detected_type, command, label)

        return exit_code
