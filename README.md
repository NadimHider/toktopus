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
* Account Rate Limits: Monitors tokens per minute (TPM) and requests per minute (RPM) against your plan limits to avoid 429 rate limit errors.
* Prompt Cache Analytics: Calculates cache hit percentages and estimated cost savings from reused prompt tokens.
* Agent Process Telemetry: Checks local language servers and background agent processes without slowing down the terminal UI.
* Frontier Model Benchmarks: Displays calibrated Coding ELO, SWE-bench Verified, and speed metrics for current frontier models.
* Agent Switching: Switch between Antigravity, Claude Code, OpenCode, Cursor, and Codex on the fly using number hotkeys.

---

## Terminal View

```text
+-----------------------------------------------------------------------------+
| :: TOKTOPUS v1.1.0 :: Universal AI Agent Monitor  [Agent: Antigravity 2.0]   |
+-----------------------------------------------------------------------------+
| [CONTEXT WINDOW & ACCOUNT LIMITS]     | [TOKEN VELOCITY & STEP BURNS]       |
| Model & Plan:    Gemini 3.8 Flash     | Session Volume:  2,302,020 total    |
|                  Google AI Pro Plan   | Composition:     [==========--------|
| Active Context:  4.2% (83k / 2,000k)  | Breakdown:       C: 2.0M In: 205k   |
| Minute Limit:    2.1% [SAFE] (4.0M)   | Velocity:        20,193 tok/step    |
| Cache Ratio:     90.9% [OPTIMAL]      | Sparkline:       ⡀⡀⠤⠶⠒⠊⠉⠑      |
+-----------------------------------------------------------------------------+
| [LIVE AI BENCHMARK INDEX] (Chatbot Arena / SWE-bench Verified)              |
| Rank   Model Name           Coding ELO   SWE-bench   HumanEval   Throughput |
| #1     GPT 6.1              1540         84.6%       98.4%       115 tok/s  |
| #2     Claude 5.5           1535         83.9%       98.1%       95 tok/s   |
| #3     DeepSeek R4.1 Flash  1495         78.4%       96.5%       240 tok/s  |
| #4     Gemini 3.8 Flash     1480         76.2%       95.8%       185 tok/s  |
| #5     Claude 3.7 Sonnet    1402         70.3%       94.8%       74 tok/s   |
+-----------------------------------------------------------------------------+
| [SUB-AGENTS & SKILLS VAULT]           | [REAL-TIME AGENT STEP TRANSCRIPT]   |
| * research            [ACTIVE]        | #111 [PLANNER_RESPONSE] 83,200 tok  |
| * team-lead           [IDLE]          | #112 [TOOL_CALL] bash  2,400 tok    |
| Skills: 374 | Plugins: 93             | #113 [PLANNER_RESPONSE] 1,120 tok   |
+-----------------------------------------------------------------------------+
| [SYSTEM LOAD & PROCESS TELEMETRY]                                           |
| Host CPU: [====--------] 14.2%  |  Host RAM: [========----] 12.4 / 32.0 GB  |
| Active Processes: Antigravity Language Server (PID 2140): CPU 1.2%          |
+-----------------------------------------------------------------------------+
| [1] Antigravity [2] Claude [3] OpenCode [4] Cursor [5] Codex | [Q] Quit    |
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
| `--benchmarks` | `-b` | Display benchmark leaderboard table and exit |
| `--rate <sec>` | `-r` | Refresh interval in seconds (default: 1.0) |
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
| `R` | Force an immediate disk rescan and UI refresh |
| `Q` | Quit back to shell |

Preferences are saved to `~/.config/toktopus/config.json`.

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
