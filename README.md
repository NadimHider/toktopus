# toktopus

A terminal monitor inspired by btop, built specifically for tracking AI coding agents in real time. It monitors active context window occupancy, account limits and rate quotas, token velocity, prompt cache efficiency, agent subprocess load, and model benchmarks across Google Antigravity, Claude Code, OpenCode v2, Cursor, and Codex.

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

## Why this exists

When running multi-turn agentic workflows, it is easy to lose track of:
* How full your active context window is getting before context truncation occurs.
* Whether prompt caching is hitting effectively or burning fresh billed tokens.
* Whether you are approaching provider rate limit boundaries (TPM and RPM) during rapid tool calls.
* How much CPU and memory local language servers and agent sidecars are consuming.

toktopus runs directly in your terminal, parsing local agent logs and system telemetry with zero lag, providing a single visual dashboard while you code.

---

## Architecture

```text
+-------------------------------------------------------------------------+
|                          AI CODING AGENTS                               |
|  +----------------+  +-------------+  +------------+  +--------------+  |
|  |  Antigravity   |  | Claude Code |  |  OpenCode  |  | Cursor/Codex |  |
|  | (brain logs,db)|  |  (sessions) |  | (local db) |  | (agent state)|  |
+--+-------+--------+--+------+------+--+-----+------+--+-------+------+--+
           |                  |               |                 |
           +------------------+-------+-------+-----------------+
                                      |
                                      v
+-------------------------------------------------------------------------+
|                        TOKTOPUS ADAPTER LAYER                           |
|       - Incremental log parsing with file seek caching                  |
|       - Non-blocking stat() checks to eliminate I/O lag                 |
|       - Session discovery and sub-agent state extraction                |
+-------------------------------------+-----------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------+
|                       CORE TELEMETRY & LIMITS                           |
|  +--------------------+  +--------------------+  +-------------------+  |
|  | Account Tier Engine|  | System Telemetry   |  | Benchmark Index   |  |
|  | (Pro, PAYG, Limits)|  | (CPU/RAM/Processes)|  | (Arena, SWE-bench)|  |
+--+--------------------+--+--------------------+--+-------------------+--+
                                      |
                                      v
+-------------------------------------------------------------------------+
|                           TERMINAL UI (RICH)                            |
|       - Active Context Window & Account Quota Limits                    |
|       - Token Velocity & Braille Burn Sparklines                        |
|       - Live AI Coding Model Benchmarks                                 |
|       - Sub-Agents & Skills Vault                                       |
|       - Real-Time Step Transcript & Process Monitoring                  |
+-------------------------------------------------------------------------+
```

---

## Visual Terminal Layout

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
| Active AI Agent Processes: Antigravity Language Server (PID 2140): CPU 1.2% |
+-----------------------------------------------------------------------------+
| [1] Antigravity [2] Claude [3] OpenCode [4] Cursor [5] Codex | [Q] Quit    |
+-----------------------------------------------------------------------------+
```

---

## Quick Install

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/nadimhider/toktopus/main/scripts/install.ps1 | iex
```

### Linux and macOS (Bash)
```bash
curl -fsSL https://raw.githubusercontent.com/nadimhider/toktopus/main/scripts/install.sh | bash
```

### Python Package Manager
```bash
pip install toktopus
# or run directly with pipx:
pipx run toktopus
```

---

## Everyday Usage

Launch live interactive terminal monitoring:
```bash
toktopus
```

### Command Line Flags

| Flag | Short | Description |
| :--- | :--- | :--- |
| `--agent <name>` | `-a` | Monitor a specific agent (`antigravity`, `claude`, `opencode`, `cursor`, `codex`, `auto`) |
| `--plan <tier>` | `-p` | Set account tier (`pro`, `payg`, `free`, `claude-pro`, `opencode-zen`, `codex-pro`) |
| `--once` | | Print a single snapshot and exit cleanly (ideal for scripts and CI) |
| `--benchmarks` | `-b` | Display the AI Coding Model Benchmark Index table and exit |
| `--rate <sec>` | `-r` | Refresh interval in seconds (default: 1.0) |
| `--version` | `-v` | Display version information |

Examples:
```bash
# Print a single telemetry snapshot and exit
toktopus --once

# Set your plan tier to Google AI Pro Plan
toktopus --plan pro

# Print current AI coding model benchmarks
toktopus --benchmarks

# Monitor OpenCode with a 0.5s refresh rate
toktopus --agent opencode --rate 0.5
```

---

## Interactive Hotkeys

Press any of these keys while running toktopus in your terminal:

| Key | Action |
| :--- | :--- |
| `1` | Switch view to Google Antigravity 2.0 (agy) |
| `2` | Switch view to Claude Code CLI (claude) |
| `3` | Switch view to OpenCode v2 / Mini (opencode) |
| `4` | Switch view to Cursor Agent (cursor) |
| `5` | Switch view to Codex / Copilot (codex) |
| `P` or `T` | Cycle account plan tier (Google AI Pro Plan, Pay-As-You-Go, Free Tier, etc.) |
| `M` | Cycle through pricing models to calculate cost comparisons |
| `B` | Toggle expanded AI Model Benchmark view |
| `R` | Force an immediate disk rescan and UI refresh |
| `Q` | Exit back to your shell |

Preferences are automatically preserved in `~/.config/toktopus/config.json`.

---

## Supported AI Coding Agents

* **Google Antigravity**: Parses local SQLite database and transcript JSONL logs directly from the active brain directory with incremental seek caching.
* **Claude Code**: Monitors session records and token history from local session storage.
* **OpenCode v2 and OpenCode Mini**: Reads local OpenCode database records and background service metrics.
* **Cursor**: Monitors active workspace agent state and background language servers.
* **Codex / Copilot**: Monitors Copilot CLI workspaces, config directories, and agent subprocesses.

---

## Supported Account Tiers

* **Google AI Pro Plan**: 2,000,000 context window, 4,000,000 TPM limit, 360 RPM rate limit, subscription quota tracking.
* **Google AI Pay-As-You-Go**: 2,000,000 context window, 4,000,000 TPM limit, 1,000 RPM, commercial API billing.
* **Google AI Free Tier**: 1,000,000 context window, 1,000,000 TPM limit, 15 RPM, free quota tracking.
* **Claude Pro Plan**: 200,000 context window, 160,000 TPM limit, 100 RPM.
* **Anthropic Tier 2+ API**: 200,000 context window, 400,000 TPM limit, 1,000 RPM.
* **OpenCode Zen Pool**: 1,000,000 context window, 2,000,000 TPM limit, 120 RPM.
* **Cursor Pro Plan**: 200,000 context window, 1,000,000 TPM limit, 200 RPM.
* **Codex / Copilot Pro**: 200,000 context window, 2,000,000 TPM limit, 300 RPM.

---

## Benchmark Index (2025 / 2026 Models)

toktopus includes calibrated benchmark records tracking:
* **Chatbot Arena Coding ELO**: Community blind evaluation on complex programming challenges.
* **SWE-bench Verified**: Real-world GitHub issue resolution percentage.
* **HumanEval**: Python functional correctness benchmark.
* **Throughput**: Generation speed measured in tokens per second.

Models tracked include GPT 6.1, Claude 5.5, DeepSeek R4.1 Flash, Gemini 3.8 Flash, Claude 3.7 Sonnet, OpenAI o3-mini, Gemini 2.5 Pro, DeepSeek-R1, and Qwen 2.5 Coder 32B.

---

## Performance & Optimization Design

1. **Non-Blocking Process Telemetry**: Windows process queries are throttled to a 3.0-second interval, matching executable names first to avoid slow command-line inspections across unrelated processes.
2. **Incremental File Caching**: Log files are checked via fast `stat()` queries. Unchanged files return cached telemetry instantly in microseconds. Appended files are read incrementally using byte offset seeking.
3. **Read-Only SQLite Operations**: SQLite connections use `mode=ro` URIs with low timeouts to avoid file locks when agents write new turns.

---

## Open Source Statement

toktopus is open source software released under the MIT License. It does not collect telemetry, send analytics, or transmit user data.

See [LICENSE](LICENSE) for full legal text.
