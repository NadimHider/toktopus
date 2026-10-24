# toktopus

A terminal monitor inspired by btop, built specifically for tracking AI coding agents in real time. It monitors token usage, context limits, prompt cache efficiency, agent subprocess load, and model benchmarks across Google Antigravity, Claude Code, OpenCode v2, and Cursor.

```text
 🐙 _       _    _                      
  | |_ ___ | | _| |_ ___  _ __  _   _ ___ 
  | __/ _ \| |/ / __/ _ \| '_ \| | | / __|
  | || (_) |   <| || (_) | |_) | |_| \__ \
   \__\___/|_|\_\\__\___/| .__/ \__,_|___/
                         |_|              
   Universal Terminal Monitor for AI Coding Agents
```

---

## Why this exists

When you spend hours inside agentic workflows, it is easy to lose track of how full your context window is getting, whether your prompt cache is actually hitting, or if a background language server is eating CPU cycles. 

Instead of opening cloud billing dashboards or digging through raw SQLite session tables, toktopus gives you a single full-screen terminal dashboard to keep an eye on everything while you code.

---

## Quick Install

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/nadimhider/toktopus/main/scripts/install.ps1 | iex
```

### Linux and macOS
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

Launch the live interactive terminal dashboard:
```bash
toktopus
```

### CLI Flags

```bash
# Print a single text snapshot and exit (useful for scripts, CI, or quick checks)
toktopus --once

# Print the AI coding benchmark matrix and exit
toktopus --benchmarks

# Monitor a specific agent directly
toktopus --agent antigravity
toktopus --agent claude
toktopus --agent opencode
toktopus --agent cursor

# Set a custom refresh rate in seconds (default is 1.0)
toktopus --rate 0.5
```

---

## Interactive Hotkeys

While running in the terminal, you can press these keys anytime:

| Key | Action |
| :--- | :--- |
| `1` | Switch live view to Google Antigravity 2.0 (agy) |
| `2` | Switch live view to Claude Code CLI (claude) |
| `3` | Switch live view to OpenCode v2 / Mini (opencode) |
| `4` | Switch live view to Cursor Agent (cursor) |
| `M` | Cycle through token pricing tiers (Gemini Flash, Pro, Claude Sonnet, DeepSeek) |
| `B` | Toggle expanded AI Model Benchmark view |
| `R` | Force an immediate disk rescan and refresh |
| `Q` | Exit back to your shell |

---

## Core Panels and Metrics

### 1. Context Window and Account Quota Limits
* **Context Gauge**: Shows your current session token usage against model boundaries (128k, 200k, or 2M). Turns yellow at 60% and red above 80% to warn you before hitting truncation.
* **Account Limits (TPM / RPM)**: Estimates your tokens per minute and requests per minute against provider tier caps so you do not get hit by 429 rate limit exceptions mid-refactor.
* **Cache Ratio and Dollars Saved**: Tracks how much of your prompt is hitting cached context versus fresh input tokens, calculating exact dollars saved.

### 2. Token Velocity and Braille Burn Sparklines
* Uses Unicode braille characters to draw a mini sparkline of token burn per turn over your last 25 steps.
* Shows average tokens consumed per step and tokens per second throughput.

### 3. Model Benchmark Index
* Tracks calibrated scores from Chatbot Arena and SWE-bench Verified (Coding ELO, HumanEval, throughput tok/s, input/output cost per 1M tokens).
* Highlights your active model with an indicator arrow so you can compare speed, capability, and price against alternatives.

### 4. Active Sub-Agents and Skills
* Shows active sub-agents (like researcher, team lead, or test automator) and their current state (ACTIVE or IDLE).
* Lists installed skill counts and active plugins.

### 5. System Load and Agent Subprocess Tracking
* Tracks host CPU and RAM utilization.
* Identifies local agent processes (language servers, opencode sidecars, claude node processes, cursor agents) and reports their individual CPU percentage and memory consumption.

---

## Supported Agents

* **Google Antigravity**: Parses local SQLite metadata and transcript JSONL logs directly from the active brain directory.
* **Claude Code**: Monitors session records and token history.
* **OpenCode v2 and OpenCode Mini**: Reads local opencode database records and background service metrics.
* **Cursor**: Monitors active workspace agent state and background language servers.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
