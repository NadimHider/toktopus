from typing import Dict, Any, List
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from toktopus.ui.charts import (
    braille_sparkline,
    context_gauge,
    quota_gauge,
    stacked_token_ratio_bar,
    mini_cpu_gauge,
    relative_benchmark_bar
)
from toktopus.core.pricing import calculate_costs
from toktopus.core.benchmarks import get_benchmarks
from toktopus.core.limits import estimate_account_limits

def build_dashboard(
    telemetry: Dict[str, Any],
    sys_metrics: Dict[str, Any],
    active_agent_key: str,
    pricing_model_key: str,
    show_full_benchmarks: bool = False
) -> Layout:
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="top_row", size=11),
        Layout(name="benchmarks", size=9 if not show_full_benchmarks else 14),
        Layout(name="middle_row", size=9),
        Layout(name="system_row", size=6),
        Layout(name="footer", size=3)
    )

    agent_name = telemetry.get("agent_name", "AI Agent")
    session_id = telemetry.get("session_id", "default")
    is_active = telemetry.get("is_active", False)
    status_icon = "🟢 ACTIVE" if is_active else "⚪ IDLE"

    header_text = Text()
    header_text.append("🐙 toktopus v1.0.0 ", style="bold #00f3ff")
    header_text.append(":: Universal AI Agent Monitor ", style="bold white")
    header_text.append(f" [Agent: {agent_name}] ", style="bold #00ff88")
    header_text.append(f" [Session: {session_id[:12]}] ", style="#b026ff")
    header_text.append(f" [{status_icon}]", style="bold #ffe600" if is_active else "dim")

    layout["header"].update(Panel(header_text, style="#00f3ff", border_style="#00f3ff"))

    layout["top_row"].split_row(
        Layout(name="context_box", ratio=1),
        Layout(name="velocity_box", ratio=1)
    )

    in_tok = telemetry.get("input_tokens", 0)
    out_tok = telemetry.get("output_tokens", 0)
    cache_tok = telemetry.get("cache_read_tokens", 0)
    max_ctx = telemetry.get("max_context_tokens", 200_000)
    used_ctx = in_tok + out_tok + cache_tok
    cache_eff = telemetry.get("cache_efficiency", 0.0)
    model_name = telemetry.get("model_name", "Gemini 3.8 Flash")

    costs = calculate_costs(in_tok, out_tok, cache_tok, pricing_model_key)
    limits = estimate_account_limits(active_agent_key, recent_tokens=in_tok + out_tok)

    context_table = Table.grid(padding=(0, 1))
    context_table.add_row("[bold white]Model:[/bold white]", f"[#00f3ff]{model_name}[/#00f3ff]")
    context_table.add_row(
        "[bold white]Context:[/bold white]",
        f"{context_gauge(used_ctx, max_ctx)} [dim]({used_ctx:,} / {max_ctx:,})[/dim]"
    )
    context_table.add_row(
        "[bold white]Account Quota:[/bold white]",
        f"{quota_gauge(limits['tpm_used'], limits['max_tpm'])} [dim]({limits['tier_name']})[/dim]"
    )
    context_table.add_row(
        "[bold white]Cache Ratio:[/bold white]",
        f"[#00ff88]{cache_eff:.1f}% [OPTIMAL][/#00ff88]" if cache_eff > 50 else f"[#ffe600]{cache_eff:.1f}%[/#ffe600]"
    )
    context_table.add_row(
        "[bold white]Composition:[/bold white]",
        f"[{stacked_token_ratio_bar(cache_tok, in_tok, out_tok)}] [dim]C/In/Out[/dim]"
    )
    context_table.add_row(
        "[bold white]Cost / Saved:[/bold white]",
        f"[#ffe600]${costs['cost_spent_usd']:.4f}[/#ffe600] spent  |  [#00ff88]${costs['cost_saved_usd']:.4f}[/#00ff88] saved 💰"
    )

    layout["top_row"]["context_box"].update(
        Panel(context_table, title="[bold #00f3ff]🧠 CONTEXT WINDOW & ACCOUNT LIMITS[/bold #00f3ff]", border_style="#00f3ff")
    )

    step_burns = telemetry.get("recent_steps_tokens", [0])
    avg_per_step = telemetry.get("tokens_per_step", 0)
    tok_per_sec = telemetry.get("tokens_per_sec", 0)
    sparkline_str = braille_sparkline(step_burns, max_width=26)

    velocity_table = Table.grid(padding=(0, 1))
    velocity_table.add_row("[bold white]Input Tokens:[/bold white]", f"[#00f3ff]{in_tok:,}[/#00f3ff] [dim]fresh billed[/dim]")
    velocity_table.add_row("[bold white]Output Tokens:[/bold white]", f"[#b026ff]{out_tok:,}[/#b026ff] [dim]agent generation[/dim]")
    velocity_table.add_row("[bold white]Cached Read:[/bold white]", f"[#00ff88]{cache_tok:,}[/#00ff88] [dim]reused context[/dim]")
    velocity_table.add_row(
        "[bold white]Velocity / Rate:[/bold white]",
        f"[#ffe600]{avg_per_step:,}[/#ffe600] tok/step  |  [#00ff88]{tok_per_sec}[/#00ff88] tok/s"
    )
    velocity_table.add_row(
        "[bold white]Burn Sparkline:[/bold white]",
        f"[#00f3ff]{sparkline_str}[/#00f3ff] [dim](recent turns)[/dim]"
    )

    layout["top_row"]["velocity_box"].update(
        Panel(velocity_table, title="[bold #b026ff]⚡ TOKEN VELOCITY & STEP BURNS[/bold #b026ff]", border_style="#b026ff")
    )

    bench_table = Table(box=None, expand=True, pad_edge=False)
    bench_table.add_column("Model", style="bold white", no_wrap=True)
    bench_table.add_column("Coding ELO", justify="right", style="#00f3ff")
    bench_table.add_column("HumanEval", justify="right", style="#00ff88")
    bench_table.add_column("SWE-bench", justify="right", style="#ffe600")
    bench_table.add_column("Throughput", justify="right", style="#b026ff")
    bench_table.add_column("Price In/Out", justify="right", style="dim")
    bench_table.add_column("Relative Index", style="#00f3ff")

    benchmarks = get_benchmarks()
    display_bench = benchmarks if show_full_benchmarks else benchmarks[:4]

    for b in display_bench:
        is_cur = (model_name.lower() in b["name"].lower()) or (b["name"].lower() in model_name.lower())
        prefix = "▶ " if is_cur else "  "
        name_style = "bold #00ff88" if is_cur else "white"

        bench_table.add_row(
            f"{prefix}{b['name']}",
            str(b["coding_elo"]),
            f"{b['humaneval']:.1f}%",
            f"{b['swe_bench']:.1f}%",
            f"{b['throughput_tps']} tok/s",
            f"${b['price_in']:.2f} / ${b['price_out']:.2f}",
            relative_benchmark_bar(b["coding_elo"]),
            style=name_style if is_cur else None
        )

    layout["benchmarks"].update(
        Panel(
            bench_table,
            title="[bold #ffe600]🏆 LIVE AI BENCHMARK INDEX (Chatbot Arena / SWE-bench / Artificial Analysis)[/bold #ffe600]",
            border_style="#ffe600"
        )
    )

    layout["middle_row"].split_row(
        Layout(name="subagents_box", ratio=4),
        Layout(name="transcript_box", ratio=6)
    )

    subagents = telemetry.get("active_subagents", [])
    sub_table = Table.grid(padding=(0, 1))
    for ag in subagents[:4]:
        status_color = "#00ff88" if ag["status"] == "ACTIVE" else "dim"
        sub_table.add_row(f"[white]• {ag['name']}[/white]", f"[{status_color}][{ag['status']}][/{status_color}]")
    sub_table.add_row("[dim]Installed Skills:[/dim] [bold #00f3ff]374[/bold #00f3ff]", "[dim]Plugins:[/dim] [bold #b026ff]93[/bold #b026ff]")

    layout["middle_row"]["subagents_box"].update(
        Panel(sub_table, title="[bold #00ff88]🛠️ SUB-AGENTS & SKILLS VAULT[/bold #00ff88]", border_style="#00ff88")
    )

    recent_steps = telemetry.get("recent_steps", [])
    step_table = Table.grid(padding=(0, 1))
    for stp in recent_steps[-3:]:
        tools_str = ", ".join(stp.get("tools", [])) or "direct prompt"
        step_table.add_row(
            f"[bold #00f3ff]#{stp.get('index', 0)}[/bold #00f3ff]",
            f"[white][{stp.get('type', 'STEP')}][/white]",
            f"[dim]{tools_str[:35]}[/dim]",
            f"[#ffe600]{stp.get('total_tokens', 0):,} tok[/#ffe600]"
        )

    layout["middle_row"]["transcript_box"].update(
        Panel(step_table, title="[bold white]📜 REAL-TIME AGENT STEP TRANSCRIPT[/bold white]", border_style="dim")
    )

    host_cpu = sys_metrics.get("host_cpu_percent", 0.0)
    host_ram_used = sys_metrics.get("host_ram_used_gb", 0.0)
    host_ram_total = sys_metrics.get("host_ram_total_gb", 32.0)
    host_ram_pct = sys_metrics.get("host_ram_percent", 0.0)
    ai_procs = sys_metrics.get("ai_processes", [])

    sys_text = Text()
    sys_text.append(f"Host CPU: [{mini_cpu_gauge(host_cpu)}] {host_cpu:.1f}%  |  ", style="white")
    sys_text.append(f"Host RAM: [{mini_cpu_gauge(host_ram_pct)}] {host_ram_used:.1f} / {host_ram_total:.1f} GB ({host_ram_pct:.1f}%)\n", style="white")
    sys_text.append("Active AI Agent Processes: ", style="bold #00f3ff")

    if ai_procs:
        proc_snippets = []
        for p in ai_procs[:3]:
            proc_snippets.append(f"{p['label']} (PID {p['pid']}): CPU {p['cpu_percent']:.1f}% | RAM {p['mem_mb']:.0f} MB")
        sys_text.append("  *  ".join(proc_snippets), style="dim")
    else:
        sys_text.append("No background AI agent processes currently active.", style="dim")

    layout["system_row"].update(
        Panel(sys_text, title="[bold #00f3ff]💻 SYSTEM LOAD & AI AGENT PROCESS TELEMETRY[/bold #00f3ff]", border_style="#00f3ff")
    )

    footer_text = Text()
    footer_text.append(" [1] Antigravity ", style="bold #00ff88" if active_agent_key == "antigravity" else "dim")
    footer_text.append(" [2] Claude Code ", style="bold #00ff88" if active_agent_key == "claude" else "dim")
    footer_text.append(" [3] OpenCode ", style="bold #00ff88" if active_agent_key == "opencode" else "dim")
    footer_text.append(" [4] Cursor ", style="bold #00ff88" if active_agent_key == "cursor" else "dim")
    footer_text.append(" | [M] Cycle Pricing  [B] Toggle Benchmarks  [R] Refresh  [Q] Quit", style="bold white")

    layout["footer"].update(Panel(footer_text, border_style="dim"))

    return layout
