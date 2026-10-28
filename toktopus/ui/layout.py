from typing import Dict, Any, List, Optional
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
    relative_benchmark_bar,
    cache_efficiency_gauge,
    cache_split_bar,
    cache_trend_sparkline,
    cost_burn_bar
)
from toktopus.core.pricing import calculate_costs, resolve_pricing_model
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
    show_full_benchmarks: bool = False,
    console_height: Optional[int] = None
) -> Layout:
    layout = Layout()

    # Dynamic row sizing
    h = console_height or 44
    if h < 34:
        top_size = 9
        mid_size = 8
        low_size = 7
        sys_size = 5
    elif h < 40:
        top_size = 10
        mid_size = 9
        low_size = 8
        sys_size = 5
    else:
        top_size = 11
        mid_size = 10
        low_size = 9
        sys_size = 6

    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="top_row", size=top_size),
        Layout(name="middle_row", size=mid_size),
        Layout(name="lower_row", size=low_size),
        Layout(name="system_row", size=sys_size),
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

    # Extract tokens
    current_ctx = telemetry.get("current_context_tokens", 0)
    max_ctx = telemetry.get("max_context_tokens", 2_000_000)
    in_tok = telemetry.get("input_tokens", 0)
    out_tok = telemetry.get("output_tokens", 0)
    cache_tok = telemetry.get("cache_read_tokens", 0)
    cache_write_tok = telemetry.get("cache_creation_tokens", 0) or telemetry.get("cache_write_tokens", 0)
    reason_tok = telemetry.get("reasoning_tokens", 0)
    total_sess_tok = telemetry.get("total_tokens", in_tok + out_tok + cache_tok + reason_tok)
    cache_eff = telemetry.get("cache_efficiency", 0.0)
    detected_model = telemetry.get("model_name", "Gemini 3.8 Flash")

    # Resolve pricing model directly from session model or explicit override
    effective_pricing_key = resolve_pricing_model(detected_model, active_agent_key, pricing_model_key)

    recent_steps = telemetry.get("recent_steps", [])
    step_burns = telemetry.get("recent_steps_tokens", [0])

    costs = calculate_costs(
        input_tokens=in_tok,
        output_tokens=out_tok,
        cache_read_tokens=cache_tok,
        model_key=effective_pricing_key,
        reasoning_tokens=reason_tok,
        cache_write_tokens=cache_write_tok,
        step_count=len(recent_steps) if recent_steps else max(1, len(step_burns)),
        elapsed_sec=elapsed_sec
    )

    agent_cost = telemetry.get("session_cost", 0.0)
    if agent_cost > 0:
        costs["cost_spent_usd"] = agent_cost

    limits = estimate_account_limits(
        active_agent_key,
        recent_tokens=current_ctx if current_ctx > 0 else (in_tok + out_tok),
        tier_override=plan_tier_key
    )
    if limits["max_context"] > 0:
        max_ctx = limits["max_context"]

    # =========================================================================
    # TOP ROW: Context Window & Quotas | Cache Hit Efficiency (Dedicated)
    # =========================================================================
    layout["top_row"].split_row(
        Layout(name="context_box", ratio=1),
        Layout(name="cache_box", ratio=1)
    )

    # 1. Context Window & Limits Panel
    context_table = Table.grid(padding=(0, 1))
    context_table.add_row(
        "[bold white]Model & Plan:[/bold white]",
        f"[#00f3ff]{detected_model}[/#00f3ff]  [bold #00ff88]{limits['tier_name']}[/bold #00ff88] [dim]{limits['plan_badge']}[/dim]"
    )
    context_table.add_row(
        "[bold white]Active Context:[/bold white]",
        f"{context_gauge(current_ctx, max_ctx)} [dim]({current_ctx:,} / {max_ctx:,})[/dim]"
    )

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
        "[bold white]Allowance Status:[/bold white]",
        f"[dim]Tier limit:[/dim] [#00ff88]{limits['max_rpd']:,} RPD[/#00ff88] [dim]|[/dim] [#ffe600]${limits.get('monthly_allowance_usd', 0.0):.2f}/mo pool[/#ffe600]"
    )

    layout["top_row"]["context_box"].update(
        Panel(context_table, title="[bold #00f3ff][CONTEXT WINDOW & ACCOUNT LIMITS][/bold #00f3ff]", border_style="#00f3ff")
    )

    # 2. DEDICATED Cache Hit Efficiency Panel (Requirement 3)
    cache_table = Table.grid(padding=(0, 1))
    cache_table.add_row(
        "[bold white]Cache Ratio Gauge:[/bold white]",
        cache_efficiency_gauge(cache_eff, width=18)
    )

    trend_spark = cache_trend_sparkline(recent_steps, max_width=20)
    cache_table.add_row(
        "[bold white]Turn Trendline:[/bold white]",
        f"[#00ff88]{trend_spark}[/#00ff88] [dim](cache hit % by turn)[/dim]"
    )

    cache_table.add_row(
        "[bold white]Token Composition:[/bold white]",
        f"{cache_split_bar(cache_tok, in_tok, width=22)} [dim]C: {cache_tok:,} | Fresh: {in_tok:,}[/dim]"
    )

    # Leverage multiplier
    total_prompt = in_tok + cache_tok
    leverage = (total_prompt / in_tok) if in_tok > 0 else 1.0
    cache_table.add_row(
        "[bold white]Prompt Leverage:[/bold white]",
        f"[bold #00ff88]{leverage:.1f}x multiplier[/bold #00ff88] [dim]({cache_tok:,} tokens avoided)[/dim]"
    )

    cache_table.add_row(
        "[bold white]Cache Cost Saved:[/bold white]",
        f"[bold #00ff88]${costs['cost_saved_usd']:.4f}[/bold #00ff88] [dim]({costs['savings_percent']}% discount)[/dim]"
    )

    layout["top_row"]["cache_box"].update(
        Panel(cache_table, title="[bold #00ff88][CACHE HIT EFFICIENCY & PROMPT LEVERAGE][/bold #00ff88]", border_style="#00ff88")
    )

    # =========================================================================
    # MIDDLE ROW: Real-Time Billing & Pricing | Token Velocity & Burns
    # =========================================================================
    layout["middle_row"].split_row(
        Layout(name="billing_box", ratio=1),
        Layout(name="velocity_box", ratio=1)
    )

    # 3. DEDICATED Session Billing & Pricing Panel (Requirement 2)
    billing_table = Table.grid(padding=(0, 1))
    billing_table.add_row(
        "[bold white]Pricing Model:[/bold white]",
        f"[#00f3ff]{costs['model_name']}[/#00f3ff] [dim]({costs['provider']})[/dim]"
    )
    billing_table.add_row(
        "[bold white]Model Rates:[/bold white]",
        f"[dim]In:[/dim] [#00f3ff]${costs['rate_in']:.2f}[/#00f3ff] [dim]| Out:[/dim] [#b026ff]${costs['rate_out']:.2f}[/#b026ff] [dim]| Cache:[/dim] [#00ff88]${costs['rate_cache']:.3f}[/#00ff88] [dim]/1M[/dim]"
    )
    billing_table.add_row(
        "[bold white]Cumulative Cost:[/bold white]",
        f"[bold #ffe600]${costs['cost_spent_usd']:.4f}[/bold #ffe600] [dim](without cache: ${costs['cost_without_cache_usd']:.4f})[/dim]"
    )

    sub_note = " [Included in Subscription]" if limits.get("is_subscription") else ""
    billing_table.add_row(
        "[bold white]Cost Breakdown:[/bold white]",
        f"[#00f3ff]In: ${costs['cost_input_usd']:.4f}[/#00f3ff] [dim]|[/dim] [#b026ff]Out: ${costs['cost_output_usd']:.4f}[/#b026ff] [dim]|[/dim] [#00ff88]Cache: ${costs['cost_cache_read_usd']:.4f}[/#00ff88]{sub_note}"
    )

    cost_step_str = f"${costs['cost_per_step_usd']:.4f}/step" if costs["cost_per_step_usd"] > 0 else "<$0.0001/step"
    burn_hr_str = f"${costs['burn_rate_hourly_usd']:.2f}/hr" if costs["burn_rate_hourly_usd"] > 0 else "$0.00/hr"
    proj_1k_str = f"${costs['projected_1k_steps_usd']:.2f}/1k turns" if costs["projected_1k_steps_usd"] > 0 else "$0.00"
    billing_table.add_row(
        "[bold white]Velocity & Proj:[/bold white]",
        f"[#ffe600]{cost_step_str}[/#ffe600]  [dim]|[/dim]  [#00ff88]{burn_hr_str}[/#00ff88]  [dim]|[/dim]  [#00f3ff]{proj_1k_str}[/#00f3ff]"
    )

    layout["middle_row"]["billing_box"].update(
        Panel(billing_table, title="[bold #ffe600][SESSION BILLING & MODEL PRICING][/bold #ffe600]", border_style="#ffe600")
    )

    # 4. Token Velocity & Burns Panel
    avg_per_step = telemetry.get("tokens_per_step", 0)
    tok_per_sec = telemetry.get("tokens_per_sec", 0)
    sparkline_str = braille_sparkline(step_burns, max_width=24)

    breakdown_parts = [
        f"[#00ff88]C: {cache_tok:,}[/#00ff88]",
        f"[#00f3ff]In: {in_tok:,}[/#00f3ff]",
        f"[#b026ff]Out: {out_tok:,}[/#b026ff]"
    ]
    if reason_tok > 0:
        breakdown_parts.append(f"[#ffe600]R: {reason_tok:,}[/#ffe600]")

    velocity_table = Table.grid(padding=(0, 1))
    velocity_table.add_row(
        "[bold white]Session Volume:[/bold white]",
        f"[bold white]{total_sess_tok:,}[/bold white] [dim]cumulative tokens processed[/dim]"
    )
    velocity_table.add_row(
        "[bold white]Composition:[/bold white]",
        f"{stacked_token_ratio_bar(cache_tok, in_tok, out_tok + reason_tok, width=24)} [dim]Cache / In / Out[/dim]"
    )
    velocity_table.add_row(
        "[bold white]Breakdown:[/bold white]",
        "  ".join(breakdown_parts)
    )
    velocity_table.add_row(
        "[bold white]Speed & Velocity:[/bold white]",
        f"[#ffe600]{avg_per_step:,}[/#ffe600] tok/step  [dim]|[/dim]  [#00ff88]{tok_per_sec}[/#00ff88] tok/s"
    )
    velocity_table.add_row(
        "[bold white]Burn Sparkline:[/bold white]",
        f"[#00f3ff]{sparkline_str}[/#00f3ff] [dim](recent turns)[/dim]"
    )

    layout["middle_row"]["velocity_box"].update(
        Panel(velocity_table, title="[bold #b026ff][TOKEN VELOCITY & STEP BURNS][/bold #b026ff]", border_style="#b026ff")
    )

    # =========================================================================
    # LOWER ROW: Full Benchmarks OR Subagents/Skills + Transcript
    # =========================================================================
    if show_full_benchmarks:
        bench_table = Table(box=None, expand=True, pad_edge=False)
        bench_table.add_column("Model", style="bold white", no_wrap=True)
        bench_table.add_column("Coding ELO", justify="right", style="#00f3ff")
        bench_table.add_column("HumanEval", justify="right", style="#00ff88")
        bench_table.add_column("SWE-bench", justify="right", style="#ffe600")
        bench_table.add_column("Throughput", justify="right", style="#b026ff")
        bench_table.add_column("Price In/Out", justify="right", style="dim")
        bench_table.add_column("Relative Index", style="#00f3ff")

        for b in get_benchmarks():
            is_cur = (detected_model.lower() in b["name"].lower()) or (b["name"].lower() in detected_model.lower())
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

        last_updated_str = get_benchmarks_last_updated()
        layout["lower_row"].update(
            Panel(bench_table, title=f"[bold #ffe600][LIVE AI BENCHMARK INDEX][/bold #ffe600] [dim](Weekly Verified : {last_updated_str})[/dim]", border_style="#ffe600")
        )
    else:
        layout["lower_row"].split_row(
            Layout(name="subagents_box", ratio=1),
            Layout(name="transcript_box", ratio=2)
        )

        sub_table = Table.grid(padding=(0, 1))
        skills_data = count_skills_and_plugins(active_agent_key)
        skills_count = skills_data.get("skills", skills_data.get("skills_count", 0))
        plugins_count = skills_data.get("plugins", skills_data.get("plugins_count", 0))

        sub_table.add_row(
            "[bold white]Skills Vault:[/bold white]",
            f"[bold #00ff88]{skills_count}[/bold #00ff88] skills  [dim]|[/dim]  [bold #00f3ff]{plugins_count}[/bold #00f3ff] plugins [dim](press [S] to manage)[/dim]"
        )

        subagents = telemetry.get("active_subagents", [])
        if subagents:
            for sa in subagents[:3]:
                st_color = "#00ff88" if sa.get("status") == "ACTIVE" else "dim"
                sub_table.add_row(
                    f"[bold white]{sa.get('name', 'subagent')}[/bold white]",
                    f"[{st_color}]{sa.get('status', 'IDLE')}[/{st_color}]"
                )
        else:
            sub_table.add_row(
                "[dim]Subagents:[/dim]",
                "[dim]No auxiliary subagents currently spawned[/dim]"
            )

        layout["lower_row"]["subagents_box"].update(
            Panel(sub_table, title="[bold #00ff88][SUB-AGENTS & SKILLS VAULT][/bold #00ff88]", border_style="#00ff88")
        )

        step_table = Table.grid(padding=(0, 1))
        if recent_steps:
            for stp in recent_steps[-3:]:
                tools_str = ", ".join(stp.get("tools", [])) or "direct turn"
                t_tok = stp.get("total_tokens", 0)
                c_tok = stp.get("cache_tokens") or stp.get("cache_read_tokens") or 0
                step_eff = f"({c_tok / t_tok * 100:.0f}% cached)" if t_tok > 0 and c_tok > 0 else ""
                step_table.add_row(
                    f"[bold #00f3ff]#{stp.get('index', 0)}[/bold #00f3ff]",
                    f"[white][{stp.get('type', 'STEP')}][/white]",
                    f"[dim]{tools_str[:32]}[/dim]",
                    f"[#ffe600]{t_tok:,} tok[/#ffe600] [dim]{step_eff}[/dim]"
                )
        else:
            step_table.add_row(
                "[dim]Transcript:[/dim]",
                "[dim]Waiting for next agent prompt/response turn...[/dim]"
            )

        layout["lower_row"]["transcript_box"].update(
            Panel(step_table, title="[bold white][REAL-TIME AGENT STEP TRANSCRIPT][/bold white]", border_style="dim")
        )

    # =========================================================================
    # SYSTEM ROW: Host CPU, RAM, GPU, Processes
    # =========================================================================
    host_cpu = sys_metrics.get("host_cpu_percent") or 0.0
    host_ram_used = sys_metrics.get("host_ram_used_gb") or 0.0
    host_ram_total = sys_metrics.get("host_ram_total_gb") or 32.0
    host_ram_pct = sys_metrics.get("host_ram_percent") or 0.0
    ai_procs = sys_metrics.get("ai_processes", [])
    gpu_data = sys_metrics.get("gpu")

    sys_text = Text()
    sys_text.append(f"Host CPU: [{mini_cpu_gauge(host_cpu)}] {host_cpu:.1f}%  |  ", style="white")
    sys_text.append(f"Host RAM: [{mini_cpu_gauge(host_ram_pct)}] {host_ram_used:.1f} / {host_ram_total:.1f} GB ({host_ram_pct:.1f}%)", style="white")

    if gpu_data:
        gpu_util = gpu_data.get("gpu_util_percent") or 0.0
        vram_used = (gpu_data.get("vram_used_mb") or 0.0) / 1024.0
        vram_total = (gpu_data.get("vram_total_mb") or 0.0) / 1024.0
        gpu_name = gpu_data.get("gpu_name") or "GPU"
        sys_text.append(f"  |  {gpu_name}: [{mini_cpu_gauge(gpu_util)}] {gpu_util:.0f}% ({vram_used:.1f}/{vram_total:.1f} GB VRAM)", style="bold #ffe600")

    sys_text.append("\nActive AI Agent Processes: ", style="bold #00f3ff")

    if ai_procs:
        proc_snippets = []
        for p in ai_procs[:3]:
            proc_snippets.append(f"{p['label']} (PID {p['pid']}): CPU {p.get('cpu_percent', 0.0):.1f}% | RAM {p.get('mem_mb', 0.0):.0f} MB")
        sys_text.append("  *  ".join(proc_snippets), style="dim")
    else:
        sys_text.append("No background AI agent processes currently active.", style="dim")

    layout["system_row"].update(
        Panel(sys_text, title="[bold #00f3ff][SYSTEM LOAD & PROCESS TELEMETRY][/bold #00f3ff]", border_style="#00f3ff")
    )

    # =========================================================================
    # FOOTER: Navigation and Hotkeys
    # =========================================================================
    footer_text = Text()
    footer_text.append(" [1] Antigravity ", style="bold #00ff88" if active_agent_key == "antigravity" else "dim")
    footer_text.append(" [2] Claude Code ", style="bold #00ff88" if active_agent_key == "claude" else "dim")
    footer_text.append(" [3] OpenCode ", style="bold #00ff88" if active_agent_key == "opencode" else "dim")
    footer_text.append(" [4] Cursor ", style="bold #00ff88" if active_agent_key == "cursor" else "dim")
    footer_text.append(" [5] Codex ", style="bold #00ff88" if active_agent_key == "codex" else "dim")
    footer_text.append(f" | [P] Plan: {limits['tier_name']}  [M] Model: {costs['model_name'][:12]}  [B] Benchmarks  [G] Space Impact  [S] Skills  [R] Refresh  [Q] Quit", style="bold white")

    layout["footer"].update(Panel(footer_text, border_style="dim"))

    return layout
