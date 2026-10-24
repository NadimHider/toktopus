# Contributing to toktopus

Thank you for your interest in contributing to toktopus. We welcome contributions including new coding agent adapters, updated benchmark index records, performance optimizations, and bug fixes.

---

## Architecture Overview

toktopus follows a decoupled, three-layer architecture:

1. **Adapters (`toktopus/adapters/`)**: Each AI coding agent implements the `BaseAgentAdapter` interface. Adapters are responsible for discovering local agent session logs, reading token counts, identifying active sub-agents, and determining whether the agent process is actively running.
2. **Core Telemetry & Limits (`toktopus/core/`)**: Handles process table polling, CPU/RAM monitoring, subscription tier limits (TPM, RPM, context window), model pricing matrices, and benchmark indexes.
3. **Terminal UI (`toktopus/ui/`)**: Renders layout panels, gauges, braille sparklines, and tables using Rich.

---

## Local Development Setup

### 1. Clone Repository and Create Virtual Environment
```bash
git clone https://github.com/nadimhider/toktopus.git
cd toktopus
python -m venv .venv
```

Activate virtual environment:
* Windows (PowerShell):
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
* Linux / macOS (Bash):
  ```bash
  source .venv/bin/activate
  ```

### 2. Install Editable Package
```bash
pip install -e .
```

### 3. Run Unit Tests
```bash
python -m unittest discover -s tests
```

---

## Guidelines for New Adapters

To add support for a new AI coding agent:

1. Create a new module in `toktopus/adapters/<agent_name>.py`.
2. Inherit from `BaseAgentAdapter` in `toktopus/adapters/base.py`.
3. Implement all four required methods:
   * `get_agent_name() -> str`
   * `is_detected() -> bool`
   * `get_active_session_id() -> Optional[str]`
   * `get_session_telemetry(session_id: Optional[str]) -> Dict[str, Any]`
4. Register the new adapter instance in `toktopus/adapters/__init__.py`.
5. Add unit test coverage in `tests/test_adapters.py`.

---

## Style Guidelines

* **Zero Emojis**: toktopus avoids emojis in terminal output, codebase, documentation, and commits to maintain consistent rendering across all terminal emulators and platforms. Use standard brackets, symbols, and ASCII badges (`[ACTIVE]`, `[IDLE]`, `[SAFE]`, `*`, `>>`, `::`).
* **Zero Em-Dashes**: Do not use unicode em-dashes or double-hyphens as em-dashes in docs or UI text. Use commas, hyphens, colons, or parentheses.
* **Non-Blocking Telemetry**: Telemetry queries run inside an interactive loop. Never execute heavy synchronous operations (such as unthrottled process table walks or unbounded file reads) on the main UI thread. Use caching and incremental offsets.

---

## Pull Request Process

1. Fork the repository and create your branch from `main`.
2. Ensure all unit tests pass:
   ```bash
   python -m unittest discover -s tests
   ```
3. Test terminal rendering manually in both interactive and snapshot mode:
   ```bash
   toktopus --once
   toktopus
   ```
4. Submit your pull request with a descriptive title and explanation of your changes.
