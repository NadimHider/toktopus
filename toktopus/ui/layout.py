from typing import Dict, Any, List
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from toktopus import __version__
from toktopus.ui.charts import (
    braille_sparkline,
    context_gauge,
    quota_gauge,
    stacked_token_ratio_bar,
    mini_cpu_gauge,
    relative_benchmark_bar
)
from toktopus.core.pricing import calculate_costs
from toktopus.core.benchmarks import get_benchmarks, get_benchmarks_last_updated
from toktopus.core.limits import estimate_account_limits
from toktopus.core.skills import count_skills_and_plugins

def _format_duration(seconds: float) -> str:
    if seconds <= 0:
        return ""
    total_sec = int(seconds)
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"

def build_dashboard(
    telemetry: Dict[str, Any],
    sys_metrics: Dict[str, Any],
    active_agent_key: str,
    pricing_model_key: str,
    plan_tier_key: str = "google-ai-pro",
    show_full_benchmarks: bool = False
) -> Layout:
    layout = Layout()

    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="top_row", size=12),
        Layout(name="benchmarks", size=9 if not show_full_benchmarks else 14),
        Layout(name="middle_row", size=9),
        Layout(name="system_row", size=6),
        Layout(name="footer", size=3)
    )

    agent_name = telemetry.get("agent_name", "AI Agent")
    session_id = telemetry.get("session_id", "default")
    is_active = telemetry.get("is_active", False)
    status_pill = "[ACTIVE]" if is_active else "[IDLE]"
    elapsed_sec = telemetry.get("session_elapsed_sec", 0.0)
    elapsed_str = _format_duration(elapsed_sec)
    time_badge = f" ({elapsed_str})" if elapsed_str else ""

    header_text = Text()
    header_text.append(f":: TOKTOPUS v{__version__} ", style="bold #00f3ff")
    header_text.append(":: Universal AI Agent Monitor ", style="bold white")
    header_text.append(f" [Agent: {agent_name}] ", style="bold #00ff88")
    header_text.append(f" [Session: {session_id[:12]}] ", style="#b026ff")
    header_text.append(f" {status_pill}{time_badge}", style="bold #00ff88" if is_active else "dim")

    layout["header"].update(Panel(header_text, style="#00f3ff", border_style="#00f3ff"))

    layout["top_row"].split_row(
        Layout(name="context_box", ratio=1),
        Layout(name="velocity_box", ratio=1)
    )

    # Active turn context tokens loaded in the window
    current_ctx = telemetry.get("current_context_tokens", 0)
    max_ctx = telemetry.get("max_context_tokens", 2_000_000)

    # Lifetime session token volume
    in_tok = telemetry.get("input_tokens", 0)
    out_tok = telemetry.get("output_tokens", 0)
    cache_tok = telemetry.get("cache_read_tokens", 0)
    total_sess_tok = telemetry.get("total_tokens", in_tok + out_tok + cache_tok)
    cache_eff = telemetry.get("cache_efficiency", 0.0)
    model_name = telemetry.get("model_name", "Gemini 3.8 Flash")

    costs = calculate_costs(in_tok, out_tok, cache_tok, pricing_model_key)
    limits = estimate_account_limits(
        active_agent_key,
        recent_tokens=current_ctx if current_ctx > 0 else (in_tok + out_tok),
        tier_override=plan_tier_key
    )

    if limits["max_context"] > 0:
        max_ctx = limits["max_context"]

    context_table = Table.grid(padding=(0, 1))
    context_table.add_row(
        "[bold white]Model & Plan:[/bold white]",
        f"[#00f3ff]{model_name}[/#00f3ff]  [bold #00ff88]{limits['tier_name']}[/bold #00ff88] [dim]{limits['plan_badge']}[/dim]"
    )
    context_table.add_row(
        "[bold white]Active Context:[/bold white]",
        f"{context_gauge(current_ctx, max_ctx)} [dim]({current_ctx:,} / {max_ctx:,})[/dim]"
    )

    # Context window warning if approaching capacity
    ctx_pct = (current_ctx / max_ctx * 100) if max_ctx > 0 else 0.0
    if ctx_pct >= 85.0:
        context_table.add_row(
            "[bold #ff3366]! CONTEXT ALERT ![/bold #ff3366]",
            f"[bold #ff3366]{ctx_pct:.1f}% used. High memory load, consider compacting session.[/bold #ff3366]"
        )

    status_color = "#00ff88" if limits["status"] == "SAFE" else ("#ffe600" if limits["status"] == "WARN" else "#ff3366")
    context_table.add_row(
        "[bold white]Minute Limit (TPM):[/bold white]",
        f"{quota_gauge(limits['tpm_used'], limits['max_tpm'])} [{status_color}][{limits['status']}][/{status_color}] [dim](Rem: {limits['tpm_remaining']:,})[/dim]"
    )
    context_table.add_row(
        "[bold white]Request Rate (RPM):[/bold white]",
        f"{quota_gauge(limits['rpm_used'], limits['max_rpm'], width=12)} [dim]({limits['rpm_used']} / {limits['max_rpm']} rpm)[/dim]"
    )
    context_table.add_row(
        "[bold white]Cache Ratio:[/bold white]",
        f"[#00ff88]{cache_eff:.1f}% [OPTIMAL][/#00ff88]" if cache_eff > 50 else f"[#ffe600]{cache_eff:.1f}%[/#ffe600]"
    )

    cost_note = " (Included in Pro Plan)" if limits.get("is_subscription") else ""
    proj_str = ""
    if elapsed_sec > 60 and costs["cost_spent_usd"] > 0:
        burn_hourly = (costs["cost_spent_usd"] / elapsed_sec) * 3600
        proj_str = f"  |  [dim]Proj:[/dim] [#ffe600]${burn_hourly:.2f}/hr[/#ffe600]"

    context_table.add_row(
        "[bold white]Session Billing:[/bold white]",
        f"[#ffe600]${costs['cost_spent_usd']:.4f}[/#ffe600] value  |  [#00ff88]${costs['cost_saved_usd']:.4f}[/#00ff88] saved{cost_note}{proj_str}"
    )

    layout["top_row"]["context_box"].update(
        Panel(context_table, title="[bold #00f3ff][CONTEXT WINDOW & ACCOUNT LIMITS][/bold #00f3ff]", border_style="#00f3ff")
    )

    step_burns = telemetry.get("recent_steps_tokens", [0])
    avg_per_step = telemetry.get("tokens_per_step", 0)
    tok_per_sec = telemetry.get("tokens_per_sec", 0)
    sparkline_str = braille_sparkline(step_burns, max_width=26)

    velocity_table = Table.grid(padding=(0, 1))
    velocity_table.add_row(
        "[bold white]Session Volume:[/bold white]",
        f"[bold white]{total_sess_tok:,}[/bold white] [dim]cumulative tokens[/dim]"
    )
    velocity_table.add_row(
        "[bold white]Composition:[/bold white]",
        f"[{stacked_token_ratio_bar(cache_tok, in_tok, out_tok)}] [dim]Cached / Fresh In / Gen Out[/dim]"
    )
    velocity_table.add_row(
        "[bold white]Breakdown:[/bold white]",
        f"[#00ff88]C: {cache_tok:,}[/#00ff88]  [#00f3ff]In: {in_tok:,}[/#00f3ff]  [#b026ff]Out: {out_tok:,}[/#b026ff]"
    )
    velocity_table.add_row(
        "[bold white]Velocity / Rate:[/bold white]",
        f"[#ffe600]{avg_per_step:,}[/#ffe600] tok/step  |  [#00ff88]{tok_per_sec}[/#00ff88] tok/s"
    )
    velocity_table.add_row(
        "[bold white]Burn Sparkline:[/bold white]",
        f"[#00f3ff]{sparkline_str}[/#00f3ff] [dim](recent turns)[/dim]"
    )

    layout["top_row"]["velocity_box"].update(
        Panel(velocity_table, title="[bold #b026ff][TOKEN VELOCITY & STEP BURNS][/bold #b026ff]", border_style="#b026ff")
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
        prefix = ">> " if is_cur else "   "
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

    updated_date = get_benchmarks_last_updated()
    layout["benchmarks"].update(
        Panel(
            bench_table,
            title=f"[bold #ffe600][LIVE AI BENCHMARK INDEX] (Weekly Verified : {updated_date})[/bold #ffe600]",
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
        sub_table.add_row(f"[white]* {ag['name']}[/white]", f"[{status_color}][{ag['status']}][/{status_color}]")

    skills_counts = count_skills_and_plugins(active_agent_key)
    sub_table.add_row(
        f"[dim]Installed Skills:[/dim] [bold #00f3ff]{skills_counts['skills']}[/bold #00f3ff]",
        f"[dim]Plugins:[/dim] [bold #b026ff]{skills_counts['plugins']}[/bold #b026ff]"
    )

    layout["middle_row"]["subagents_box"].update(
        Panel(sub_table, title="[bold #00ff88][SUB-AGENTS & SKILLS VAULT][/bold #00ff88]", border_style="#00ff88")
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
        Panel(step_table, title="[bold white][REAL-TIME AGENT STEP TRANSCRIPT][/bold white]", border_style="dim")
    )

    host_cpu = sys_metrics.get("host_cpu_percent", 0.0)
    host_ram_used = sys_metrics.get("host_ram_used_gb", 0.0)
    host_ram_total = sys_metrics.get("host_ram_total_gb", 32.0)
    host_ram_pct = sys_metrics.get("host_ram_percent", 0.0)
    ai_procs = sys_metrics.get("ai_processes", [])
    gpu_data = sys_metrics.get("gpu")

    sys_text = Text()
    sys_text.append(f"Host CPU: [{mini_cpu_gauge(host_cpu)}] {host_cpu:.1f}%  |  ", style="white")
    sys_text.append(f"Host RAM: [{mini_cpu_gauge(host_ram_pct)}] {host_ram_used:.1f} / {host_ram_total:.1f} GB ({host_ram_pct:.1f}%)", style="white")

    if gpu_data:
        gpu_util = gpu_data.get("gpu_util_percent", 0.0)
        vram_used = gpu_data.get("vram_used_mb", 0.0) / 1024.0
        vram_total = gpu_data.get("vram_total_mb", 0.0) / 1024.0
        sys_text.append(f"  |  GPU: [{mini_cpu_gauge(gpu_util)}] {gpu_util:.0f}% ({vram_used:.1f}/{vram_total:.1f} GB VRAM)", style="bold #ffe600")

    sys_text.append("\nActive AI Agent Processes: ", style="bold #00f3ff")

    if ai_procs:
        proc_snippets = []
        for p in ai_procs[:3]:
            proc_snippets.append(f"{p['label']} (PID {p['pid']}): CPU {p['cpu_percent']:.1f}% | RAM {p['mem_mb']:.0f} MB")
        sys_text.append("  *  ".join(proc_snippets), style="dim")
    else:
        sys_text.append("No background AI agent processes currently active.", style="dim")

    layout["system_row"].update(
        Panel(sys_text, title="[bold #00f3ff][SYSTEM LOAD & PROCESS TELEMETRY][/bold #00f3ff]", border_style="#00f3ff")
    )

    footer_text = Text()
    footer_text.append(" [1] Antigravity ", style="bold #00ff88" if active_agent_key == "antigravity" else "dim")
    footer_text.append(" [2] Claude Code ", style="bold #00ff88" if active_agent_key == "claude" else "dim")
    footer_text.append(" [3] OpenCode ", style="bold #00ff88" if active_agent_key == "opencode" else "dim")
    footer_text.append(" [4] Cursor ", style="bold #00ff88" if active_agent_key == "cursor" else "dim")
    footer_text.append(" [5] Codex ", style="bold #00ff88" if active_agent_key == "codex" else "dim")
    footer_text.append(f" | [P] Plan: {limits['tier_name']}  [M] Model  [B] Benchmarks  [R] Refresh  [Q] Quit", style="bold white")

    layout["footer"].update(Panel(footer_text, border_style="dim"))

    return layout
