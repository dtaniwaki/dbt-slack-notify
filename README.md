# dbt-slack-notify

Slack notification wrapper CLI for dbt builds.

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
| `--type` | Notification type: `dbt-seed`, `dbt-run`, `dbt-test`, `auto` (default: `auto`) |
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

### Auto detection

When `--type` is `auto` (default), the notification type is detected from the command:

- `dbt run ...` -> `dbt-run`
- `dbt test ...` -> `dbt-test`
- `dbt seed ...` -> `dbt-seed`
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

> **Note**: When using `--type dbt-run`, the tool automatically runs `dbt ls` to preview the selected models. Ephemeral models are excluded via `--exclude config.materialized:ephemeral`. If your dbt command already includes `--exclude`, the two `--exclude` flags will be combined by dbt (AND semantics), which may narrow the model list more than expected.

## License

MIT
