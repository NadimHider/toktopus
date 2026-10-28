# toktopus

toktopus is a personal hobby project I built to monitor token usage, active context windows, and account limits in real time while working with AI coding agents. It supports Google Antigravity, Claude Code, OpenCode, Cursor, and Codex.

```text
  _       _    _                      
 | |_ ___ | | _| |_ ___  _ __  _   _ ___ 
 | __/ _ \| |/ / __/ _ \| '_ \| | | / __|
 | || (_) |   <| || (_) | |_) | |_| \__ \
  \__\___/|_|\_\\__\___/| .__/ \__,_|___/
                        |_|              
   Universal Terminal Monitor for AI Coding Agents
```

---

## Features

* Active Context Tracking: Shows memory load for the current prompt turn against model boundaries (like the 2M token window on Google AI Pro Plan) without mixing in past turn totals.
* Dedicated Session Billing & Model Pricing: Displays live input, output, and cache rates per 1M tokens, calculates cumulative session spend vs spend without caching, per-step cost, hourly burn rate velocity, and projected 1k turn expenses.
* Dedicated Cache Hit Efficiency & Prompt Leverage: Real-time cache ratio gauge with optimal/efficient badges, turn-by-turn braille sparkline, token composition bar, and prompt leverage multiplier tracking how many tokens you avoided paying full price for.
* Retro Space Impact Terminal Arcade Game: Play a retro space shooter directly in your terminal with spaceship controls, lasers, scout aliens, interceptors, heavy fighters, asteroids, boss waves, HP bar, and scoring.
* Cross-Agent Skill Modifier: Inspect, edit, append, prepend, replace, or copy skills across Antigravity, Claude Code, OpenCode, Cursor, and Codex with automatic YAML frontmatter preservation and backup protection.
* Reasoning Token Breakdown: Captures thinking and reasoning tokens across DeepSeek R1/V4, Mimo, and Gemini Thinking models without discarding them from output totals.
* Context Utilization Warnings: Triggers an in-terminal alert whenever active context usage reaches 85% or higher so you can compact the session before hitting boundaries.
* Session Elapsed Timer: Displays how long your current agent session has been active directly in the header bar.
* Live Account Rate Limits: Monitors tokens per minute (TPM) and requests per minute (RPM) against your plan limits to avoid 429 rate limit errors.
* Agent Process & System Telemetry: Checks background agent processes and hardware metrics without slowing down the terminal UI, including optional GPU VRAM and utilization metrics.
* Real Skills & Plugin Inventory: Dynamically counts your installed skills and plugins directly from the filesystem with a cached disk scanner.
* Frontier Model Benchmarks: Displays weekly-calibrated Coding ELO, SWE-bench Verified, and throughput metrics for current frontier models.
* Telemetry Export: Export instantaneous session snapshots as clean JSON files for scripting, CI runs, or usage auditing.
* Agent Switching: Switch between Antigravity, Claude Code, OpenCode, Cursor, and Codex on the fly using number hotkeys or via the `--agent` command-line flag.

---

## Terminal View

```text
+-----------------------------------------------------------------------------+
| :: TOKTOPUS v1.4.0 :: Universal AI Agent Monitor  [Agent: Antigravity 2.0]   |
+-----------------------------------------------------------------------------+
| [CONTEXT WINDOW & ACCOUNT LIMITS]     | [CACHE HIT EFFICIENCY & LEVERAGE]   |
| Model & Plan:    Gemini 3.8 Flash     | Cache Ratio:     96.2% [OPTIMAL]    |
|                  Google AI Pro Plan   | Turn Trendline:  ......             |
| Active Context:  4.4% (87k / 2,000k)  | Composition:     [==========-----]  |
| Minute Limit:    2.1% [SAFE] (4.0M)   | Leverage:        26.1x multiplier   |
| Request Rate:    12 / 360 rpm         | Cache Saved:     $8.40 (70.6% off)  |
+-----------------------------------------------------------------------------+
| [SESSION BILLING & MODEL PRICING]     | [TOKEN VELOCITY & STEP BURNS]       |
| Pricing Model:   Gemini 3.8 Flash     | Session Volume:  119,699,377 total  |
| Model Rates:     In: $0.10 | Out:     | Composition:     Cache / In / Out   |
|                  $0.40 | Cache: $0.025| Breakdown:       C: 114M In: 4.5M   |
| Cumulative Cost: $3.5035              | Velocity:        87,505 tok/step    |
| Velocity & Proj: $0.029/step | $42/1k | Sparkline:       ..........         |
+-----------------------------------------------------------------------------+
| [SUB-AGENTS & SKILLS VAULT]           | [REAL-TIME AGENT STEP TRANSCRIPT]   |
| Skills Vault: 488 skills | 115 plugins| #1828 [PLANNER_RESP] 87k (97% cache)|
| * research            [ACTIVE]        | #1829 [TOOL_CALL] bash 2,400 tok    |
| * team-lead           [IDLE]          | #1830 [PLANNER_RESP] 88k (97% cache)|
+-----------------------------------------------------------------------------+
| [SYSTEM LOAD & PROCESS TELEMETRY]                                           |
| Host CPU: [====--------] 14.2%  |  Host RAM: [========----] 12.4 / 32.0 GB  |
| Active Processes: Antigravity Language Server (PID 2140): CPU 1.2%          |
+-----------------------------------------------------------------------------+
| [1] Antigravity [2] Claude [3] OpenCode [4] Cursor [5] Codex | [G] Game [Q] |
+-----------------------------------------------------------------------------+
```

---

## Installation

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/NadimHider/toktopus/main/scripts/install.ps1 | iex
```

### Linux and macOS (Bash)
```bash
curl -fsSL https://raw.githubusercontent.com/NadimHider/toktopus/main/scripts/install.sh | bash
```

### Python Package
```bash
pip install toktopus
# or run directly with pipx:
pipx run toktopus
```

---

## Usage

Start live monitoring:
```bash
toktopus
```

### Flags

| Flag | Short | Description |
| :--- | :--- | :--- |
| `--agent <name>` | `-a` | Select active agent (`antigravity`, `claude`, `opencode`, `cursor`, `codex`, `auto`) |
| `--plan <tier>` | `-p` | Set active plan tier (`pro`, `payg`, `free`, `claude-pro`, `opencode-zen`, `codex-pro`) |
| `--once` | | Output a single snapshot and exit (useful for scripts) |
| `--export <path>` | `-e` | Export current telemetry snapshot as JSON to file and exit |
| `--benchmarks` | `-b` | Display benchmark leaderboard table and exit |
| `--game`, `--space-impact` | | Launch the retro Space Impact terminal arcade game and exit |
| `--skills`, `--list-skills` | | List installed agent skills across coding harnesses and exit |
| `--get-skill <name>` | | Inspect and print the contents of a specific skill |
| `--modify-skill <name>` | | Modify or append instructions to an existing installed skill |
| `--instruction <text>` | | Instruction content to append or apply when modifying a skill |
| `--mode <mode>` | | Modification mode: `append`, `prepend`, or `replace` (default: append) |
| `--copy-skill <name>` | | Copy an installed skill to another agent harness |
| `--to-agent <agent>` | | Target agent harness when copying a skill (`antigravity`, `claude`, `opencode`, etc.) |
| `--rate <sec>` | `-r` | Refresh interval in seconds (default: 1.0) |
| `--no-color` | | Disable color styling (also respects NO_COLOR env var) |
| `--version` | `-v` | Display version information |

---

## Hotkeys

| Key | Action |
| :--- | :--- |
| `1` | Switch view to Antigravity 2.0 (`agy`) |
| `2` | Switch view to Claude Code CLI (`claude`) |
| `3` | Switch view to OpenCode v2 / Mini (`opencode`) |
| `4` | Switch view to Cursor Agent (`cursor`) |
| `5` | Switch view to Codex / Copilot CLI (`codex`) |
| `P` or `T` | Cycle plan tier (Google AI Pro Plan, Pay-As-You-Go, Free Tier, etc.) |
| `M` | Cycle pricing models to compare theoretical token costs |
| `B` | Toggle expanded benchmark table |
| `G` | Launch retro Space Impact arcade game from the monitor |
| `S` | Open installed skills vault summary |
| `R` | Force an immediate disk rescan and UI refresh |
| `Q` | Quit back to shell |

Preferences are saved to `~/.config/toktopus/config.json`.

---

## Retro Space Impact Game

toktopus v1.4.0 includes an arcade space shooter built directly into the terminal. Play it while waiting for long agent runs or debugging sessions:

```bash
toktopus --game
```

Or press `G` from inside the live monitoring dashboard.

Controls:
* `W` / `A` / `S` / `D` or Arrow Keys: Maneuver ship
* `Space`: Fire laser cannon
* `P`: Pause game
* `Q` or `Esc`: Exit back to monitor or terminal
* `R`: Restart game upon game over

---

## Cross-Agent Skill Management

Inspect, modify, and migrate skills across any installed agent harness:

```bash
# List all installed skills across all harnesses
toktopus --skills

# Inspect instructions and metadata for a specific skill
toktopus --get-skill workflow-patterns

# Append new instructions to an existing skill (creates automatic .bak backup)
toktopus --modify-skill workflow-patterns --instruction "Always run tests before completing."

# Replace a skill entirely
toktopus --modify-skill custom-linter --instruction "Run ruff check ." --mode replace

# Copy a skill from Antigravity to Claude Code
toktopus --copy-skill workflow-patterns --to-agent claude
```

---

## Supported Agents and Plans

| Agent | Default Plan | Context Window | TPM Limit | RPM Limit |
| :--- | :--- | :--- | :--- | :--- |
| Google Antigravity | Google AI Pro Plan | 2,000,000 | 4,000,000 | 360 |
| Claude Code | Claude Pro Plan | 200,000 | 160,000 | 100 |
| OpenCode v2 / Mini | OpenCode Zen Pool | 1,000,000 | 2,000,000 | 120 |
| Cursor | Cursor Pro Plan | 200,000 | 1,000,000 | 200 |
| Codex / Copilot | Codex Pro Plan | 200,000 | 2,000,000 | 300 |

Other supported tiers include Google AI Pay-As-You-Go, Google AI Free Tier, and Anthropic API Tier 2+.

---

## Weekly Benchmark and Pricing Updates

Benchmark evaluations (Chatbot Arena Coding ELO, SWE-bench Verified) and provider pricing models change frequently.

I update the benchmark index in `data/benchmarks.json` and model pricing tables in `toktopus/core/pricing.py` weekly to reflect newly released models and leaderboard shifts. When online, toktopus refreshes these numbers directly from the repository.

---

## Configuration

Settings are saved in `~/.config/toktopus/config.json`:

```json
{
  "active_agent": "antigravity",
  "plan_tier": "google-ai-pro",
  "pricing_model": "gemini-3.8-flash",
  "refresh_rate": 1.0,
  "show_benchmarks": false
}
```

---

## Questions and Feedback

This is a personal hobby project. If you have questions, run into bugs, or have ideas for improvements, open an issue or reach out to me directly:
* Email: nadim.hider@outlook.com

---

## License

MIT License. See [LICENSE](LICENSE) for details.
