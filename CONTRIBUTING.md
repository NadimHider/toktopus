# Contributing to toktopus

toktopus is a personal hobby project. Contributions are welcome, especially for new agent adapters, benchmark updates, and bug fixes.

---

## Architecture

The codebase has three main parts:

1. Adapters (`toktopus/adapters/`): Each supported coding agent implements `BaseAgentAdapter` to read local session logs, token usage, and process status.
2. Core Logic (`toktopus/core/`): Handles process monitoring, rate limits (TPM and RPM), pricing calculations, and benchmark data.
3. Terminal UI (`toktopus/ui/`): Renders panels, gauges, braille sparklines, and tables using Rich.

---

## Local Setup

1. Clone and create a virtual environment:
```bash
git clone https://github.com/NadimHider/toktopus.git
cd toktopus
python -m venv .venv
```

Activate the environment:
* Windows (PowerShell): `.venv\Scripts\Activate.ps1`
* Linux / macOS (Bash): `source .venv/bin/activate`

2. Install in editable mode:
```bash
pip install -e .
```

3. Run the test suite:
```bash
python -m unittest discover -s tests
```

---

## Adding an Adapter

To add support for a new coding agent:
1. Create `toktopus/adapters/<name>.py` inheriting from `BaseAgentAdapter`.
2. Implement `get_agent_name`, `is_detected`, `get_active_session_id`, and `get_session_telemetry`.
3. Register it in `toktopus/adapters/__init__.py`.
4. Add tests in `tests/test_adapters.py`.

---

## Style Guidelines

* Zero Emojis: toktopus uses standard console glyphs (`[ACTIVE]`, `[IDLE]`, `*`, `>>`, `::`) so rendering is clean and consistent across all terminal emulators.
* Zero Em-Dashes: Do not use em-dashes in docs or UI text. Use commas, hyphens, colons, or parentheses.
* Non-Blocking I/O: Telemetry queries run inside an interactive loop. Avoid blocking disk or process operations.

---

## Questions

Feel free to open an issue or reach out to me directly at nadim.hider@outlook.com.
