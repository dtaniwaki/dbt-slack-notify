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
| `--timeout` | Timeout for the wrapped command (e.g. `240m`, `4h`, `3600`). On timeout the child is sent `SIGINT` then `SIGKILL` after `--kill-grace` |
| `--kill-grace` | Seconds to wait after `SIGINT` before `SIGKILL` (e.g. `300`, `5m`, default: `300`) |
| `--progress-step` | Post a progress update to the thread each time this many percent more of the run completes, parsed from dbt's `N of M` output (e.g. `10`). Disabled if unset |
| `--progress-min-nodes` | Suppress a progress update unless at least this many nodes finished since the last one. Avoids per-node spam on small runs |
| `--progress-min-interval` | Suppress a progress update unless at least this long elapsed since the last one (e.g. `60s`, `2m`). Throttles fast runs |

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

### Timeout

Use `--timeout` instead of wrapping the command with GNU `timeout`:

```bash
dbt-slack-notify --timeout 240m dbt build --selector daily
```

On timeout the tool sends `SIGINT` to the command's process group (not `SIGTERM`), so dbt shuts down gracefully and flushes `run_results.json` for the nodes that finished — enabling a follow-up re-run of only the unfinished nodes. If the process is still alive after `--kill-grace` seconds it is force-killed with `SIGKILL`. When a timeout occurs the tool posts the timeout alarm and, if `run_results.json` is present, the usual result summary. The timed-out run exits with code `124`.

### Progress updates

Long-running commands can feel silent between the start and finish notifications. Pass `--progress-step` to post interim updates to the same thread as the run progresses:

```bash
dbt-slack-notify --progress-step 10 dbt build --selector daily
```

The tool parses dbt's `N of M` streaming output and posts a compact reply each time another `--progress-step` percent of the run completes (e.g. `dbt run 進捗: 120/200件 (60%) — :warning: エラー2件`). Because the trigger is percent-based, the number of updates is capped at `100 / step` regardless of how many nodes run.

Two gates suppress noise on small or fast runs; an update is posted only after every gate has cleared since the previous one (the interval is measured from the run start, so nothing posts during the first window):

- `--progress-min-nodes N` — require at least `N` nodes to finish between updates. On a run smaller than `N`, no interim updates are posted at all (only start and finish).
- `--progress-min-interval DURATION` — require at least `DURATION` (e.g. `60s`, `2m`) between updates. **Defaults to `300s` (5 min) when `--progress-step` is set**, so short runs stay quiet; pass a smaller value to loosen it.

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
| `DBT_SLACK_NOTIFY_PROGRESS_STEP` | `PROGRESS_STEP` | Percent step for progress updates (see `--progress-step`) |
| `DBT_SLACK_NOTIFY_PROGRESS_MIN_NODES` | `PROGRESS_MIN_NODES` | Minimum nodes between progress updates |
| `DBT_SLACK_NOTIFY_PROGRESS_MIN_INTERVAL` | `PROGRESS_MIN_INTERVAL` | Minimum time between progress updates (e.g. `60s`) |

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
