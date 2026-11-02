# Toktopus User Guide

[Back to the project README](../README.md)

## Install or update

Requires Python 3.9 or newer. Use an interactive terminal for the live dashboard.

Install the v1.7.0 release directly from GitHub:

```bash
python -m pip install --upgrade "git+https://github.com/NadimHider/toktopus.git@v1.7.0"
python -m toktopus
```

This installation method requires Git. You can also install the wheel attached to the [release](https://github.com/NadimHider/toktopus/releases/tag/v1.7.0) with `python -m pip install --upgrade PATH_TO_WHEEL`.

The `toktopus` command is available when Python's scripts directory is on your PATH. Otherwise, use `python -m toktopus`, which runs the same application.

To work from a checkout:

```bash
git clone https://github.com/NadimHider/toktopus.git
cd toktopus
python -m pip install .
python -m toktopus
```

To update an existing checkout on `main`:

```bash
git pull --ff-only
python -m pip install --upgrade .
```

## What is new in v1.7.0

- Local SQLite session history with metadata search and paging.
- Selectable tool timelines with observed status, available timestamps, failure counts, and repeated-activity hints.
- Automatic history collection from detected local agents every five seconds. Selected-agent telemetry is cached for two seconds.
- Local OTLP JSON imports with trace, span, parent, duration, and available token metadata.
- LiveNerf Model Health with explicit refresh, a validated local cache, source provenance, and offline fallback.
- Diagnostics for missing sources and unsupported database schemas.
- Corrected Codex token accounting, an OpenCode session/message/part reader, and removal of fabricated activity and token speeds.
- Unavailable account quotas are shown explicitly. Estimated costs are separated from actual billing.

Read the [release notes](releases/v1.7.0.md) for compatibility details.

## Dashboard controls

| Key | Action |
| --- | --- |
| `1` to `6` | Select Antigravity, Claude Code, OpenCode, Cursor, Codex, or Pi |
| `J` | Open History or return from a timeline to History |
| `[` / `]` | Select a session on the current History page |
| `Enter` | Open the selected session's observed timeline |
| `N` / `P` | History: next/previous page. Timeline: older/newer events |
| `D` | Open Diagnostics; press again to return to Overview |
| `H` | Open cached Model Health; press again to return to Overview |
| `R` | Invalidate the telemetry cache and refresh the selected agent |
| `M` | Cycle the estimated pricing model |
| `P` in Overview | Cycle legacy configured plan estimates |
| `B` | Toggle the bundled benchmark view |
| `S` / `E` | Expand skills or open the skill editor |
| `O` / `G` | Open the companion lounge or terminal game |
| `F` / `T` | Feed or pet the companion |
| `Q` | Quit |

History and timeline pages show six rows in the live dashboard. Command-line views support larger pages and metadata search.

## History and timelines

```bash
python -m toktopus --history
python -m toktopus --history --search codex
python -m toktopus --history --limit 20 --offset 20
python -m toktopus --timeline SESSION_ID --agent codex
python -m toktopus --timeline SESSION_ID --agent claude --limit 20 --offset 20
python -m toktopus --no-history
```

History stores the latest session snapshot rather than adding cumulative counters every time the dashboard refreshes. Repeated observations update existing events. Sessions are ordered by source activity time when available, and by observation time otherwise.

The timeline displays available tool evidence. Explicit tool errors and exit codes drive failure counts. Three consecutive events naming the same tools produce a repeated-activity hint, not a finding that the agent is definitely stuck.

Toktopus records observations while it runs. It does not automatically rebuild every past session, and polling can miss events between reads. Native tool details currently have the strongest coverage in Claude Code, Codex, and the supported OpenCode database schema. A timeline is an inspection view, not a rerun of the agent.

## Import OpenTelemetry traces

```bash
python -m toktopus --import-otlp trace.json
python -m toktopus --history --search otel:
python -m toktopus --timeline TRACE_ID --agent otel:SERVICE_NAME
```

The importer accepts OTLP JSON documents with `resourceSpans`, `scopeSpans`, and `spans`. It reads standard `gen_ai` usage and tool metadata, retains parent span IDs, and calculates duration when both timestamps exist. Missing counters remain unavailable. Nested span counters are not summed into an invented session total.

Imports are limited to 8 MB and 10,000 spans. Prompts, tool arguments, outputs, and arbitrary span attributes are omitted from the history store. This release does not start an OTLP network receiver or automatically instrument unrelated applications.

## Model Health with LiveNerf

```bash
python -m toktopus --refresh-model-health
python -m toktopus --model-health
```

The first command downloads public [LiveNerf results](https://github.com/ninjahawk/livenerf). The second reads the cached copy without network access. The `H` dashboard view is also offline.

Model Health shows recent aggregate observations, benchmark-family detail in the command-line view, sample counts, errors, and available output-token medians. Provenance includes the source URL, retrieval time, content SHA-256, CLI version, and harness hash. Failed refreshes preserve the last valid cached data. Retrievals older than 48 hours are marked stale.

Toktopus does not run LiveNerf benchmarks or infer a statistical degradation verdict from a daily score. Upstream observations do not measure the quality of your own coding session. Aggregate and family rows overlap and are never added together.

## Agent coverage and diagnostics

| Agent | Available local source | Limitations |
| --- | --- | --- |
| Antigravity | Available local session logs and metadata | Format and timing availability vary by installed version |
| Claude Code | Local project/session records and JSONL tool events | Bounded recent-file discovery; not a complete historical import |
| OpenCode | Read-only session/message/part database reader, with legacy schema fallback | Unsupported schemas report diagnostics; context occupancy is unavailable |
| Cursor | Available local tracking records | Best effort; some usage and tool details are not recorded locally |
| Codex | Local rollout JSONL and session index | Separate from GitHub Copilot; token timing may be unavailable |
| Pi | Legacy local JSON records | Current Pi coding-agent JSONL support remains future work |

```bash
python -m toktopus --diagnostics --agent opencode
python -m toktopus --once --agent codex
python -m toktopus --export telemetry.json --agent claude
```

Account quotas are unavailable without a verified source. Local token totals cannot establish account-wide usage, billing, or remaining subscription capacity. Costs use configured pricing or an agent-reported estimate and are not an authoritative bill. Missing throughput and context measurements remain unavailable.

Host CPU, memory, disk, network, process, and available GPU metrics describe the local machine. They do not establish which agent caused every system change.

## Storage and privacy

Toktopus uses these local files:

| File | Purpose |
| --- | --- |
| `~/.config/toktopus/config.json` | Dashboard settings |
| `~/.config/toktopus/history.sqlite3` | Session snapshots and observed event metadata |
| `~/.config/toktopus/livenerf.json` | Cached public benchmark results |

History retains at most 2,000 sessions and 50,000 events. Row limits do not guarantee a fixed SQLite file size. Stop the app before manually removing its history database.

History omits prompts, tool arguments, and tool outputs. Session IDs, model names, tool names, timestamps, and other retained metadata can still be sensitive. Existing adapters read local source records, and snapshot exports can include session and host details. Review exports before sharing them.

Use `--no-history` to disable recording and automatic background discovery for that run. Normal monitoring does not upload telemetry, inspect credential stores, change agent authentication, install certificates, or run model evaluations.

## Other tools

The app also includes a skill vault, bundled benchmark table, companion lounge, terminal Space Impact game, and a standalone browser game. The bundled benchmark table is separate from LiveNerf and should not be treated as a live capability measurement.

```bash
python -m toktopus --skills
python -m toktopus --benchmarks
python -m toktopus --pet
python -m toktopus --game
python -m toktopus --web-game
python -m toktopus --help
```

The skill editor can modify installed skills when explicitly used. Browser and terminal game scores are stored separately. Use `--no-color` or `NO_COLOR=1` for plain output.

## Development

```bash
python -m pip install .
python -m unittest discover -s tests
python -m pip install ruff build
python -m ruff check toktopus tests
python -m build
```

The runtime depends on Rich and psutil. Local storage, imports, and public result fetching use the Python standard library. CI runs tests on Linux, Windows, and macOS across supported Python versions.

See [reference research and remaining work](OBSERVABILITY-RESEARCH.md) for the observability-platform comparison, source coverage, and roadmap. This release does not claim feature parity with all referenced platforms.

