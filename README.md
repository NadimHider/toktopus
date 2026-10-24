# toktopus

A terminal monitor inspired by btop, built specifically for tracking AI coding agents in real time. It monitors active context window occupancy, account limits and rate quotas, token velocity, prompt cache efficiency, agent subprocess load, and model benchmarks across Google Antigravity, Claude Code, OpenCode v2, and Cursor.

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

When running long coding agent sessions, it is easy to lose track of how full your context window is getting, whether prompt caching is working, or whether you are approaching provider rate limits (TPM and RPM).

Instead of opening cloud billing dashboards or digging through log files, toktopus gives you a single full-screen terminal dashboard to keep an eye on everything while you code.

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

# Set your account tier or subscription plan (e.g. pro, payg, free, claude-pro)
toktopus --plan pro

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
| `P` or `T` | Cycle account tier (Google AI Pro Plan, Pay-As-You-Go, Free Tier, etc.) |
| `M` | Cycle through token pricing models (Gemini Flash, Pro, Claude Sonnet, DeepSeek) |
| `B` | Toggle expanded AI Model Benchmark view |
| `R` | Force an immediate disk rescan and refresh |
| `Q` | Exit back to your shell |

Your selected plan, agent, and pricing preferences are automatically saved to `~/.config/toktopus/config.json`.

---

## Core Panels and Metrics

### 1. Context Window and Account Quota Limits
* **Active Context Window**: Tracks current turn memory load against model context boundaries (e.g. 2,000,000 tokens on Google AI Pro Plan). Gauges turn yellow at 60% and red above 80% to warn before context truncation occurs.
* **Account Limits (TPM / RPM)**: Monitors tokens per minute and requests per minute against your specific subscription tier (Google AI Pro Plan, Tier 1 Pay-As-You-Go, Anthropic Tier 2+, or OpenCode Zen) to avoid 429 rate limit errors.
* **Cache Ratio and Dollars Saved**: Measures prompt cache reuse percentage and computes dollar value saved on cached turns.

### 2. Token Velocity and Braille Burn Sparklines
* Uses Unicode braille characters to draw a mini sparkline of token burn per turn over your last 25 steps.
* Displays cumulative session token volume, fresh input vs cached reads vs generated outputs, and throughput tokens per second.

### 3. Model Benchmark Index
* Tracks calibrated scores from Chatbot Arena and SWE-bench Verified (Coding ELO, HumanEval, throughput tok/s, input/output pricing).
* Highlights your active model with an indicator arrow so you can compare speed, capability, and price against alternatives.

### 4. Active Sub-Agents and Skills
* Shows active sub-agents (like researcher, team lead, or test automator) and their current state ([ACTIVE] or [IDLE]).
* Lists installed skill counts and active plugins from your local environment.

### 5. System Load and Agent Subprocess Tracking
* Tracks host CPU and RAM utilization.
* Identifies local agent processes (language servers, opencode sidecars, claude node processes, cursor agents) and reports their individual CPU percentage and memory consumption without blocking the UI loop.

---

## Supported Agents

* **Google Antigravity**: Parses local SQLite metadata and transcript JSONL logs directly from the active brain directory with incremental caching.
* **Claude Code**: Monitors session records and token history.
* **OpenCode v2 and OpenCode Mini**: Reads local opencode database records and background service metrics.
* **Cursor**: Monitors active workspace agent state and background language servers.

---

## Supported Account Tiers

* **Google AI Pro Plan**: 2M context window, 4,000,000 TPM limit, 360 RPM, subscription quota tracking.
* **Google AI Pay-As-You-Go**: 2M context window, 4,000,000 TPM limit, 1,000 RPM, commercial API billing.
* **Google AI Free Tier**: 1M context window, 1,000,000 TPM limit, 15 RPM, free quota tracking.
* **Claude Pro Plan**: 200k context window, 160,000 TPM limit, 100 RPM.
* **Anthropic Tier 2+ API**: 200k context window, 400,000 TPM limit, 1,000 RPM.
* **OpenCode Zen Pool**: 1M context window, 2,000,000 TPM limit, 120 RPM.
* **Cursor Pro Plan**: 200k context window, 1,000,000 TPM limit, 200 RPM.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
