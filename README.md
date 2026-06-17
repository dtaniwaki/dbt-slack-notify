# dbt-slack-notify

A CLI wrapper that sends Slack notifications for `dbt` builds. Wrap any `dbt run`, `dbt test`, `dbt seed`, or `dbt build` command and get:

- **Start / finish notifications** posted to a Slack channel (threaded)
- **Result summaries** — success/error/skip counts per resource type, elapsed time
- **Error details** — failed node names and messages (up to 5, with truncation)
- **Node list preview** — for `dbt run` uploads the model list; for `dbt build` posts up to 3 start notifications (seed / model / test) each with its own `dbt ls` preview
- **Auto type detection** — detects `run` / `test` / `seed` / `build` from the command, no manual `--type` needed

## Installation

```bash
pip install dbt-slack-notify
```

## Usage

```bash
dbt-slack-notify dbt run --selector incremental
dbt-slack-notify dbt test --selector incremental
dbt-slack-notify --type dbt-test --label Elementary dbt test --selector elementary
```

### Options

**Notification**

| Option | Description |
|---|---|
| `--type` | Notification type: `dbt-seed`, `dbt-run`, `dbt-test`, `dbt-build`, `auto` (default: `auto`) |
| `--label` | Label appended to notification title (e.g. `Elementary` -> `dbt test (Elementary)`) |

**Slack**

| Option | Description |
|---|---|
| `--slack-token` | Slack API token (overrides env var) |
| `--slack-channel` | Slack channel (overrides env var) |
| `--slack-thread-ts` | Existing Slack thread timestamp to reply to |

**dbt**

| Option | Description |
|---|---|
| `--dbt-project-dir` | dbt project directory (overrides env var) |
| `--dbt-target-path` | dbt target path (overrides env var) |

**General**

| Option | Description |
|---|---|
| `--log-level` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`) |
| `--log-file` | Log file path |
| `--state-file` | State file path (default: `$TMPDIR/dbt_slack_notify_state.json`) |

### Auto type detection

When `--type` is `auto` (default), the notification type is detected from the command:

- `dbt run ...` -> `dbt-run`
- `dbt test ...` -> `dbt-test`
- `dbt seed ...` -> `dbt-seed`
- `dbt build ...` -> `dbt-build`
- otherwise -> posts the command string as a message

## Environment Variables

**Slack**

| Variable | Fallback | Description |
|---|---|---|
| `DBT_SLACK_NOTIFY_SLACK_TOKEN` | `SLACK_TOKEN` | Slack API token |
| `DBT_SLACK_NOTIFY_SLACK_CHANNEL` | `SLACK_CHANNEL` | Slack channel to post to |

**dbt**

| Variable | Fallback | Description |
|---|---|---|
| `DBT_SLACK_NOTIFY_DBT_PROJECT_DIR` | `DBT_PROJECT_DIR` | dbt project directory |
| `DBT_SLACK_NOTIFY_DBT_TARGET_PATH` | `DBT_TARGET_PATH` | dbt target path |

**General**

| Variable | Fallback | Description |
|---|---|---|
| `DBT_SLACK_NOTIFY_LOG_LEVEL` | `LOG_LEVEL` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `DBT_SLACK_NOTIFY_LOG_FILE` | `LOG_FILE` | Log file path |
| `DBT_SLACK_NOTIFY_STATE_FILE` | `STATE_FILE` | State file path |

> **Note**: In production environments, prefer environment variables over `--slack-token` CLI option to avoid token exposure in process lists.

> **Note**: When using `--type dbt-run`, the tool runs `dbt ls --resource-type model` to preview the selected models. For `--type dbt-build`, it runs `dbt ls` once per resource type (`seed`, `model`, `test`) and posts one start notification per non-empty category. Ephemeral models are excluded from the model preview via `--exclude config.materialized:ephemeral`. If your dbt command already includes `--exclude`, the two `--exclude` flags will be combined by dbt (AND semantics), which may narrow the list more than expected.

## Development

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

Run tests, linter, and type checker via [nox](https://nox.thea.codes/):

```bash
uv run nox -s test     # pytest across Python 3.11–3.13
uv run nox -s lint      # ruff
uv run nox -s typecheck # mypy
```

Or run tests directly:

```bash
uv run pytest tests/ -q
```

## License

MIT
