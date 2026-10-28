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

* Autonomous Cyber-Octopus Pet ("Tokto"): An interactive companion living in your terminal monitor. Tokto streams tokens, wiggles tentacles when coding, wears cyber sunglasses during elite cache hits, nods off to sleep when idle, quips funny coding thoughts, and levels up as you digest tokens.
* Interactive Pet Controls: Press `F` to drop crunchy token snacks (`+30 Fuel`), press `T` to give scratches (`+25 Joy`), or press `O` / `--pet` to enter the full-screen aquarium Pet Lounge habitat!
* 300ms Ultra-Fast Auto-Refresh: Cycles at 3.33 FPS (every 300 milliseconds) for fluid ASCII animations, instant gauge updates, and real-time telemetry with cached non-blocking I/O.
* High-Resolution Rounded TUI: Beautiful cybernetic neon aesthetic with rounded borders, fractional progress bars (`▏▎▍▌▋▊▉█`), humanized token formatting (`136.2K / 2.0M`), and responsive width adaptation.
* Active Context Tracking: Shows memory load for the current prompt turn against model boundaries (like the 2M token window on Google AI Pro Plan) without mixing in past turn totals.
* Dedicated Session Billing & Model Pricing: Displays live input, output, and cache rates per 1M tokens, calculates cumulative session spend vs spend without caching, per-step cost, hourly burn rate velocity, and projected 1k turn expenses.
* Dedicated Cache Hit Efficiency & Prompt Leverage: Real-time cache ratio gauge with optimal/efficient badges, turn-by-turn braille sparkline, token composition bar, and prompt leverage multiplier tracking how many tokens you avoided paying full price for.
* Retro Space Impact Terminal Arcade Game: Play a retro space shooter directly in your terminal with spaceship controls, lasers, scout aliens, interceptors, heavy fighters, asteroids, boss waves, HP bar, and scoring.
* Cross-Agent Skill Modifier: Inspect, edit, append, prepend, replace, or copy skills across Antigravity, Claude Code, OpenCode, Cursor, and Codex with automatic YAML frontmatter preservation and backup protection.
* Reasoning Token Breakdown: Captures thinking and reasoning tokens across DeepSeek R1/V4, Mimo, and Gemini Thinking models without discarding them from output totals.
* Context Utilization Warnings: Triggers an in-terminal alert whenever active context usage reaches 85% or higher so you can compact the session before hitting boundaries.
* Live Account Rate Limits: Monitors tokens per minute (TPM) and requests per minute (RPM) against your plan limits to avoid 429 rate limit errors.
* Agent Process & System Telemetry: Checks background agent processes and hardware metrics without slowing down the terminal UI, including optional GPU VRAM and utilization metrics.
* Frontier Model Benchmarks: Displays weekly-calibrated Coding ELO, SWE-bench Verified, and throughput metrics for current frontier models.
* Telemetry Export: Export instantaneous session snapshots as clean JSON files for scripting, CI runs, or usage auditing.

---

## Terminal View

```text
+-----------------------------------------------------------------------------+
| :: TOKTOPUS v1.5.0 :: Universal AI Agent Monitor  [Agent: Antigravity 2.0]   |
+-----------------------------------------------------------------------------+
| [CONTEXT & LIMITS]        | [CACHE & LEVERAGE]        | [TOKTO COMPANION]   |
| Model:  Gemini 3.8 Flash  | Ratio:  96.2% [OPTIMAL]   |    .---.    Tokto   |
| Plan:   [PRO PLAN]        | Trend:  ...... (cache %)  |   / >O< \   (Lv.2)  |
| Context:[████░░░░░░] 9.9% | Split:  C: 125M | In: 4M  |  (|  W  |)  [STREAM]|
| Minute: 5.0% [SAFE] (3.8M)| Leverage: 26.1x multiplier|   \~/~\~/   Fuel 75%|
| Request:12 / 360 rpm      | Saved:  +$8.40 (70.6% off)|  [F] Feed [T] Pet   |
+-----------------------------------------------------------------------------+
| [SESSION BILLING & PRICING]           | [TOKEN VELOCITY & BURNS]            |
| Model:   Gemini 3.8 Flash (DeepMind)  | Session Volume: 131.2M total tokens |
| Rates:   In: $0.10 | Out: $0.40 | C:  | Composition:    Cache / In / Out    |
| Spend:   $3.6455 (Without Cache $12)  | Breakdown:      C: 125M  In: 4.9M   |
| Proj:    $0.029/step | $0.85/hr       | Speed:          136k tok/step       |
+-----------------------------------------------------------------------------+
| [SUB-AGENTS & SKILLS VAULT]           | [REAL-TIME AGENT STEP TRANSCRIPT]   |
| Skills Vault: 488 skills | 115 plugins| #1991 [PLANNER_RESP] 196k (99% cache|
| * research            [ACTIVE]        | #1992 [TOOL_CALL] bash 1,200 tok    |
| * team-lead           [IDLE]          | #1993 [PLANNER_RESP] 198k (99% cache|
+-----------------------------------------------------------------------------+
| [SYSTEM LOAD & PROCESS TELEMETRY]                                           |
| Host CPU: [====--------] 14.2%  |  Host RAM: [========----] 12.4 / 32.0 GB  |
| Active Processes: Antigravity Language Server (PID 2140): CPU 1.2%          |
+-----------------------------------------------------------------------------+
| [1-5] Agent [P] Plan [M] Model [B] Bench [G] Game [O] Pet [F] Feed [Q] Quit |
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

Start live monitoring (defaults to 300 millisecond refresh):
```bash
toktopus
```

### Flags

| Flag | Short | Description |
| :--- | :--- | :--- |
| `--agent <name>` | `-a` | Select active agent (`antigravity`, `claude`, `opencode`, `cursor`, `codex`, `auto`) |
| `--plan <tier>` | `-p` | Set active plan tier (`pro`, `payg`, `free`, `claude-pro`, `opencode-zen`, `codex-pro`) |
| `--rate <sec>` | `-r` | Refresh interval in seconds (default: 0.3 for 300ms) |
| `--pet`, `--pet-lounge` | | Enter the full-screen interactive Tokto Pet Lounge habitat and exit |
| `--game`, `--space-impact` | | Launch the retro Space Impact terminal arcade game and exit |
| `--skills`, `--list-skills` | | List installed agent skills across coding harnesses and exit |
| `--get-skill <name>` | | Inspect and print the contents of a specific skill |
| `--modify-skill <name>` | | Modify or append instructions to an existing installed skill |
| `--instruction <text>` | | Instruction content to append or apply when modifying a skill |
| `--mode <mode>` | | Modification mode: `append`, `prepend`, or `replace` (default: append) |
| `--copy-skill <name>` | | Copy an installed skill to another agent harness |
| `--to-agent <agent>` | | Target agent harness when copying a skill |
| `--once` | | Output a single snapshot and exit (useful for scripts) |
| `--export <path>` | `-e` | Export current telemetry snapshot as JSON to file and exit |
| `--benchmarks` | `-b` | Display benchmark leaderboard table and exit |
| `--no-color` | | Disable color styling (also respects NO_COLOR env var) |
| `--version` | `-v` | Display version information |

---

## Hotkeys

| Key | Action |
| :--- | :--- |
| `1` - `5` | Switch active agent (1: Antigravity, 2: Claude, 3: OpenCode, 4: Cursor, 5: Codex) |
| `F` | Feed Tokto a token snack (+30 Fuel, +15 Joy) |
| `T` | Pet Tokto (+25 Joy) |
| `O` | Open full-screen Tokto Pet Lounge aquarium habitat |
| `G` | Launch retro Space Impact arcade game from the monitor |
| `P` | Cycle plan tier (Google AI Pro Plan, Pay-As-You-Go, Free Tier, etc.) |
| `M` | Cycle pricing models to compare theoretical token costs |
| `B` | Toggle expanded benchmark table |
| `S` | Open installed skills vault summary |
| `R` | Force an immediate disk rescan and UI refresh |
| `Q` | Quit back to shell |

Preferences are saved to `~/.config/toktopus/config.json`.

---

## Tokto: Autonomous Cyber-Octopus Pet

toktopus v1.5.0 introduces Tokto, an autonomous interactive companion who lives in your monitor:

* Autonomous state machine: watches your streaming tokens, dances when cache hits are high, gets hungry if neglected, and falls asleep when coding sessions pause.
* Real-time quips: shares humorous coding thoughts in live speech bubbles.
* Level progression: Tokto gains XP as you burn and digest tokens!
* Interactive keys: press `F` to drop treats or `T` to pet anytime in the live dashboard.
* Full-screen Aquarium Habitat:
  ```bash
  toktopus --pet
  ```
  Or press `O` while the monitor is running to swim around, drop snacks, and explore Tokto's cyber habitat.

---

## Retro Space Impact Game

Play a retro arcade shooter directly in your terminal while waiting for long agent runs:

```bash
toktopus --game
```

Or press `G` from inside the live monitoring dashboard.

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

## Questions and Feedback

This is a personal hobby project. If you have questions, run into bugs, or have ideas for improvements, open an issue or reach out to me directly:
* Email: nadim.hider@outlook.com

---

## License

MIT License. See [LICENSE](LICENSE) for details.
