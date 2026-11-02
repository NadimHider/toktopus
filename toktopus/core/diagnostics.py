"""Read-only diagnostics for local telemetry; never inspect credentials."""
import time

from rich.panel import Panel
from rich.table import Table


def render_diagnostics(telemetry, agent_key):
    table = Table(expand=True, title="Local telemetry diagnostics")
    table.add_column("Check")
    table.add_column("Result")
    session = telemetry.get("session_id")
    table.add_row("Agent", agent_key)
    table.add_row("Session", str(session or "Unavailable"))
    modified = telemetry.get("last_modified", 0) or 0
    age = f"{max(0, int(time.time() - modified))} seconds ago" if modified else "Unavailable"
    table.add_row("Source last modified", age)
    table.add_row("Scope", "Locally observed sessions; other devices are excluded")
    table.add_row("Account quota / billing", "Unavailable: no account integration")
    table.add_row("Cost", "Estimated API-equivalent cost; not a subscription bill")
    table.add_row("Reader status", str(telemetry.get("diagnostic_error") or telemetry.get("data_status", "Local reader; availability varies by agent version")))
    table.add_row("Recovery", "Update the agent, select the correct agent (1-6), then press R")
    return Panel(table, subtitle="D Overview | H Model Health | Q Quit")
