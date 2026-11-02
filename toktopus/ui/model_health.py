"""Terminal view of public benchmark observations, separate from local usage."""
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def render_model_health(snapshot, compact=False):
    rows = snapshot.get("rows", [])
    fetched = snapshot.get("fetched_at") or "never"
    state = "stale" if snapshot.get("stale") else "cached"
    summary = Text(f"Public upstream results | {state} | Retrieved: {fetched}\n")
    summary.append("These observations do not measure your own coding sessions. A daily score is not proof of degradation.\n")
    if not compact:
        summary.append("Source: " + snapshot.get("source", "LiveNerf") + "\n", style="dim")
    if snapshot.get("sha256") and not compact:
        summary.append("Content SHA-256: " + snapshot["sha256"] + "\n", style="dim")
    if snapshot.get("error"):
        summary.append(snapshot["error"] + "\n", style="yellow")
    if not rows:
        summary.append("No cached results. Run toktopus --model-health --refresh-model-health to fetch public data.")
        return Panel(summary, title="Model Health · LiveNerf", subtitle="H Overview | J History | D Diagnostics | Q Quit")
    table = Table(expand=True)
    columns = ("Date", "Model / arm", "Family", "Score", "Scored / samples", "Errors")
    if not compact:
        columns += ("Median output", "Harness / CLI")
    for name in columns:
        table.add_column(name)
    # Show aggregate trends separately; never add family rows to their aggregate.
    latest_date = max(row["date_utc"] for row in rows)
    visible = [row for row in rows if row["family"] == "all"][-10:]
    visible += [row for row in rows if row["date_utc"] == latest_date and row["family"] != "all"]
    if compact:
        visible = [row for row in rows if row['family'] == 'all'][-4:]
    for row in visible:
        cells = [row["date_utc"], Text(row["model"] + " / " + row["arm"]), Text(row["family"]), f"{row['score']:.1%}", f"{row['scored']} / {row['samples']}", str(row["errors"])]
        if not compact:
            cells += [f"{row['output_tokens_median']:,.0f}", Text(row["harness_hash"] + " / " + row["cli_version"])]
        table.add_row(*cells)
    note = Text("Recent aggregate observations and latest family breakdown. Samples overlap across aggregate and family rows; they are not summed.\nFunding and runner metadata are retained in the cached records. No statistical drift verdict is inferred here.", style="dim")
    if compact:
        note = Text('Latest aggregate observations. Run --model-health for family breakdown and provenance. No statistical drift verdict is inferred here.', style='dim')
    return Panel(Group(summary, table, note), title="Model Health · LiveNerf", border_style="cyan", subtitle="H Overview | J History | D Diagnostics | Q Quit")
