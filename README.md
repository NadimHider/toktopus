# toktopus

toktopus is a personal hobby project I built to monitor token usage, active context windows, and account limits in real time while working with AI coding agents. It supports Google Antigravity, Claude Code, OpenCode, Cursor, Codex, and Pi Agent.

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

* Collapsible Cross-Agent Skill Vault: Positioned directly beneath stats. Defaults to a compact cross-agent overview across Antigravity, Claude, OpenCode, Cursor, Codex, and Pi. Press `S` to expand into an interactive skill table or press `E` to edit instructions in-place with automatic `.md.bak` backups.
* Automated Model and Subscription Plan Extraction: Dynamically detects currently active models and subscription plans across all agents (Antigravity `settings.json`, Claude `~/.claude.json`, Codex rollouts, OpenCode SQLite, Cursor `state.vscdb`, Pi session config) so you never have to manually configure plans.
* Upgraded Autonomous Cyber-Pet ("Tokto"): An interactive companion living in your terminal monitor. Tokto features articulated tentacles, cute animated expressions, cyber-shades during elite cache hits, XP progression bars, fuel/joy status, and real-time speech bubbles.
* Interactive Pet Controls: Press `F` to drop crunchy token snacks (`+30 Fuel`), press `T` to give scratches (`+25 Joy`), or press `O` / `--pet` to enter the full-screen aquarium Pet Lounge habitat.
* High-Impact Cache and Leverage Visualizations: High-resolution meters (`large_cache_gauge`), 24-turn Braille trend sparklines, multi-tier token composition fuel tank (Cache, In, Out, Reasoning), and net cash savings multipliers.
* Extended System Hardware Telemetry: Comprehensive host monitoring tracking CPU frequency (MHz), physical and logical core counts, RAM, Swap memory used/total, Disk storage free/used GB, Network I/O sent/received MB, and GPU metrics.
* Universal Agent Support: Seamless hotkey switching between Google Antigravity (`1`), Claude Code (`2`), OpenCode (`3`), Cursor (`4`), Codex (`5`), and Pi Agent (`6`).
* 300ms Ultra-Fast Auto-Refresh: Cycles at 3.33 FPS (every 300 milliseconds) for fluid ASCII animations, instant gauge updates, and real-time telemetry with cached non-blocking I/O.
* Retro Space Impact Terminal Arcade Game: Play a retro space shooter directly in your terminal with spaceship controls, lasers, scout aliens, interceptors, heavy fighters, asteroids, boss waves, HP bar, and scoring.
* Dedicated Session Billing and Model Pricing: Displays live input, output, and cache rates per 1M tokens, calculates cumulative session spend vs spend without caching, per-step cost, hourly burn rate velocity, and projected 1k turn expenses.
* Context Utilization Warnings: Triggers an in-terminal alert whenever active context usage reaches 85% or higher so you can compact the session before hitting boundaries.
* Frontier Model Benchmarks: Displays weekly-calibrated Coding ELO, SWE-bench Verified, and throughput metrics for current frontier models.
* Telemetry Export: Export instantaneous session snapshots as clean JSON files for scripting, CI runs, or usage auditing.

---

## Terminal View

```text
+-----------------------------------------------------------------------------+
| :: TOKTOPUS v1.6.0 :: Universal AI Agent Monitor  [Agent: Antigravity 2.0]   |
+-----------------------------------------------------------------------------+
| [CONTEXT & LIMITS]        | [CACHE & LEVERAGE]        | [TOKTO COMPANION]   |
| Model:  Gemini 3.8 Flash  | Ratio:  96.5% [ELITE]     |    .-------.  Tokto |
| Plan:   [PRO PLAN]        | Trend:  ...... (cache %)  |   /  >   <  \ (Lv.2)|
| Context:[████░░░░░░] 8.8% | Split:  C: 145M | In: 5M  |  (|   ===   |)[STRM]|
| Minute: 4.4% [SAFE] (3.8M)| Leverage: 28.4x multiplier|   /|\/~~~\/|\ XP 60%|
| Request:12 / 360 rpm      | Saved:  +$9.20 (74% off)  |  [F] Feed [T] Pet   |
+-----------------------------------------------------------------------------+
| [SESSION BILLING & PRICING]           | [TOKEN VELOCITY & BURNS]            |
| Model:   Gemini 3.8 Flash (DeepMind)  | Session Volume: 151.3M total tokens |
| Rates:   In: $0.10 | Out: $0.40 | C:  | Tank:       [█████████████░░░░]     |
| Spend:   $3.8520 (Without Cache $14)  | Breakdown:  C: 145M In: 5.3M Out: 1M|
| Proj:    $0.028/step | $0.82/hr       | Speed:      142k tok/step           |
+-----------------------------------------------------------------------------+
| [SKILLS VAULT : CROSS-AGENT OVERVIEW (COLLAPSED)]                           |
| Antigravity: 86 sk | Claude: 188 sk | OpenCode: 1 sk | Cursor: 2 sk | Pi: 5 |
| [Press 'S' to Expand/Inspect | 'E' to Edit Skill] -- Active: Antigravity    |
+-----------------------------------------------------------------------------+
| [REAL-TIME AGENT STEP TRANSCRIPT]                                           |
| #2269 [PLANNER_RESPONSE] run_command    174.3K tok (98% cached)             |
| #2270 [GENERIC]          direct turn    0 tok                               |
| #2271 [PLANNER_RESPONSE] run_command    176.9K tok (98% cached)             |
+-----------------------------------------------------------------------------+
| [EXTENDED SYSTEM HARDWARE & PROCESS TELEMETRY]                              |
| Host CPU: [====------] 18.2% @ 3408MHz (4P/4L) | RAM: [====------] 12.8GB  |
| Disk: [====------] 432GB / 930GB (Free 498GB)  | Net: Up 986MB / Down 4.6GB|
| Active Processes: Antigravity (PID 5968): CPU 1.2% | OpenCode (PID 17308)   |
+-----------------------------------------------------------------------------+
| [1-6] Agent [P] Plan [M] Model [B] Bench [S] Skills [E] Edit [G] Game [Q]   |
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
| `--agent <name>` | `-a` | Select active agent (`antigravity`, `claude`, `opencode`, `cursor`, `codex`, `pi`, `auto`) |
| `--plan <tier>` | `-p` | Set active plan tier (`pro`, `payg`, `free`, `claude-pro`, `opencode-zen`, `codex-pro`, `pi-pro`) |
| `--rate <sec>` | `-r` | Refresh interval in seconds (default: 0.3 for 300ms) |
| `--pet`, `--pet-lounge` | | Enter the full-screen interactive Tokto Pet Lounge habitat and exit |
| `--game`, `--space-impact` | | Launch the retro Space Impact terminal arcade game and exit |
| `--skills`, `--list-skills` | | List installed agent skills across coding harnesses and exit |
| `--get-skill <name>` | | Inspect and print the contents of a specific skill |
| `--modify-skill <name>` | | Modify or append instructions to an existing installed skill |
| `--instruction <text>` | | Instruction content to append or apply when modifying a skill |
| `--mode <mode>` | | Modification mode: `append`, `prepend`, or `replace` (default: append) |
| `--copy-skill <name>` | | Copy an installed skill to another agent harness |
| `--to-agent <agent>` | | Target agent harness when copying a skill (`antigravity`, `claude`, `opencode`, `cursor`, `codex`, `pi`) |
| `--once` | | Output a single snapshot and exit (useful for scripts) |
| `--export <path>` | `-e` | Export current telemetry snapshot as JSON to file and exit |
| `--benchmarks` | `-b` | Display benchmark leaderboard table and exit |
| `--no-color` | | Disable color styling (also respects NO_COLOR env var) |
| `--version` | `-v` | Display version information |

---

## Hotkeys

| Key | Action |
| :--- | :--- |
| `1` - `6` | Switch active agent (1: Antigravity, 2: Claude, 3: OpenCode, 4: Cursor, 5: Codex, 6: Pi) |
| `S` | Toggle collapsible / expandable Skill Vault directly beneath stats |
| `E` | In-place interactive skill editor (modify or append skill instructions) |
| `F` | Feed Tokto a token snack (+30 Fuel, +15 Joy) |
| `T` | Pet Tokto (+25 Joy) |
| `O` | Open full-screen Tokto Pet Lounge aquarium habitat |
| `G` | Launch retro Space Impact arcade game from the monitor |
| `P` | Cycle plan tier (Google AI Pro Plan, Pay-As-You-Go, Free Tier, etc.) |
| `M` | Cycle pricing models to compare theoretical token costs |
| `B` | Toggle expanded benchmark table |
| `R` | Force an immediate disk rescan and UI refresh |
| `Q` | Quit back to shell |

Preferences are saved to `~/.config/toktopus/config.json`.

---

## Tokto: Autonomous Cyber-Octopus Pet

toktopus v1.6.0 introduces an upgraded Tokto design with articulated tentacles and level XP progress:

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
