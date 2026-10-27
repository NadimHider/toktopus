import os
import sys
import time
import json
import argparse
from rich.console import Console
from rich.live import Live

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from toktopus import __version__
from toktopus.ui.theme import THEME_CONFIG
from toktopus.ui.layout import build_dashboard
from toktopus.adapters import KEY_MAP, get_adapter, auto_detect_active_agent
from toktopus.core.system import get_system_telemetry
from toktopus.core.keyboard import get_pressed_key, init_keyboard, restore_keyboard
from toktopus.core.pricing import PRICING_TABLE, calculate_costs
from toktopus.core.benchmarks import get_benchmarks, get_benchmarks_last_updated
from toktopus.core.limits import normalize_plan_key, get_next_plan, estimate_account_limits
from toktopus.core.config import load_config, save_config

console = Console(theme=THEME_CONFIG)

PRICING_KEYS = list(PRICING_TABLE.keys())

def print_benchmarks_table():
    from rich.table import Table
    from toktopus.ui.charts import relative_benchmark_bar

    updated_date = get_benchmarks_last_updated()
    table = Table(title=f":: TOKTOPUS : AI Coding Model Benchmark Index (Weekly Verified : {updated_date}) ::", border_style="#ffe600")
    table.add_column("Rank", justify="center", style="dim")
    table.add_column("Model Name", style="bold white")
    table.add_column("Provider", style="#b026ff")
    table.add_column("Coding ELO", justify="right", style="bold #00f3ff")
    table.add_column("SWE-bench", justify="right", style="#ffe600")
    table.add_column("HumanEval", justify="right", style="#00ff88")
    table.add_column("Speed", justify="right", style="white")
    table.add_column("Price (In/Out 1M)", justify="right", style="dim")
    table.add_column("Relative Rating", style="#00f3ff")

    for m in get_benchmarks():
        table.add_row(
            f"#{m['rank']}",
            m["name"],
            m["provider"],
            str(m["coding_elo"]),
            f"{m['swe_bench']:.1f}%",
            f"{m['humaneval']:.1f}%",
            f"{m['throughput_tps']} tok/s",
            f"${m['price_in']:.2f} / ${m['price_out']:.2f}",
            relative_benchmark_bar(m["coding_elo"])
        )

    console.print(table)

def export_telemetry_snapshot(export_path: str, telemetry: dict, sys_metrics: dict, agent_key: str, plan_tier: str, pricing_key: str):
    in_tok = telemetry.get("input_tokens", 0)
    out_tok = telemetry.get("output_tokens", 0)
    cache_tok = telemetry.get("cache_read_tokens", 0)
    reason_tok = telemetry.get("reasoning_tokens", 0)
    current_ctx = telemetry.get("current_context_tokens", 0)

    costs = calculate_costs(in_tok, out_tok + reason_tok, cache_tok, pricing_key)
    agent_cost = telemetry.get("session_cost", 0.0)
    if agent_cost > 0:
        costs["cost_spent_usd"] = agent_cost

    limits = estimate_account_limits(
        agent_key,
        recent_tokens=current_ctx if current_ctx > 0 else (in_tok + out_tok),
        tier_override=plan_tier
    )

    snapshot_data = {
        "version": __version__,
        "timestamp_epoch": time.time(),
        "agent": {
            "key": agent_key,
            "name": telemetry.get("agent_name", agent_key),
            "session_id": telemetry.get("session_id", "default"),
            "model_name": telemetry.get("model_name"),
            "is_active": telemetry.get("is_active", False),
            "session_elapsed_sec": telemetry.get("session_elapsed_sec", 0.0)
        },
        "tokens": {
            "current_context": current_ctx,
            "max_context": limits.get("max_context", 2_000_000),
            "input": in_tok,
            "output": out_tok,
            "cache_read": cache_tok,
            "reasoning": reason_tok,
            "total_session": telemetry.get("total_tokens", in_tok + out_tok + cache_tok + reason_tok),
            "cache_efficiency_pct": telemetry.get("cache_efficiency", 0.0),
            "tokens_per_step": telemetry.get("tokens_per_step", 0),
            "tokens_per_sec": telemetry.get("tokens_per_sec", 0)
        },
        "account_limits": limits,
        "billing": costs,
        "system": {
            "host_cpu_percent": sys_metrics.get("host_cpu_percent"),
            "host_ram_used_gb": sys_metrics.get("host_ram_used_gb"),
            "host_ram_total_gb": sys_metrics.get("host_ram_total_gb"),
            "host_ram_percent": sys_metrics.get("host_ram_percent"),
            "ai_processes": sys_metrics.get("ai_processes", []),
            "gpu": sys_metrics.get("gpu")
        }
    }

    out_file = os.path.abspath(export_path)
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(snapshot_data, f, indent=2)

    console.print(f"[bold #00ff88]:: Exported telemetry snapshot to {out_file} ::[/bold #00ff88]")

def main():
    saved_cfg = load_config()

    parser = argparse.ArgumentParser(
        prog="toktopus",
        description="Universal Terminal Monitor for AI Coding Agents"
    )
    parser.add_argument(
        "--agent", "-a",
        choices=["antigravity", "claude", "opencode", "cursor", "codex", "auto"],
        default=saved_cfg.get("active_agent", "auto"),
        help="Target AI agent to monitor (default: saved config or auto)"
    )
    parser.add_argument(
        "--plan", "-p",
        default=None,
        help="Account tier or subscription plan (e.g. pro, free, payg, claude-tier2)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Print single telemetry snapshot and exit"
    )
    parser.add_argument(
        "--export", "-e",
        metavar="PATH",
        help="Export telemetry snapshot as a JSON file and exit"
    )
    parser.add_argument(
        "--benchmarks", "-b",
        action="store_true",
        help="Display AI Model Benchmark Index and exit"
    )
    parser.add_argument(
        "--rate", "-r",
        type=float,
        default=float(saved_cfg.get("refresh_rate", 1.0)),
        help="Refresh interval in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output (also respects NO_COLOR env var)"
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"toktopus v{__version__}"
    )

    args = parser.parse_args()

    if args.no_color or os.environ.get("NO_COLOR"):
        console.no_color = True

    if args.benchmarks:
        print_benchmarks_table()
        sys.exit(0)

    if args.agent == "auto":
        active_agent_key = auto_detect_active_agent()
    else:
        active_agent_key = args.agent

    if args.plan:
        plan_tier = normalize_plan_key(args.plan, active_agent_key)
        save_config({"plan_tier": plan_tier})
    else:
        plan_tier = normalize_plan_key(saved_cfg.get("plan_tier", "google-ai-pro"), active_agent_key)

    saved_pricing = saved_cfg.get("pricing_model", "gemini-3.8-flash")
    current_pricing_idx = PRICING_KEYS.index(saved_pricing) if saved_pricing in PRICING_KEYS else 0
    show_full_benchmarks = bool(saved_cfg.get("show_benchmarks", False))

    adapter = get_adapter(active_agent_key)
    telemetry = adapter.get_session_telemetry()
    sys_metrics = get_system_telemetry()

    if args.export:
        export_telemetry_snapshot(args.export, telemetry, sys_metrics, active_agent_key, plan_tier, PRICING_KEYS[current_pricing_idx])
        sys.exit(0)

    if args.once:
        dashboard = build_dashboard(
            telemetry,
            sys_metrics,
            active_agent_key,
            PRICING_KEYS[current_pricing_idx],
            plan_tier_key=plan_tier,
            show_full_benchmarks=False,
            console_height=console.size.height
        )
        console.print(dashboard)
        sys.exit(0)

    init_keyboard()
    try:
        with Live(console=console, screen=True, auto_refresh=False) as live:
            last_refresh = 0.0

            while True:
                now = time.time()

                key = get_pressed_key()
                if key == "q":
                    break
                elif key in KEY_MAP:
                    active_agent_key = KEY_MAP[key]
                    adapter = get_adapter(active_agent_key)
                    plan_tier = normalize_plan_key(plan_tier, active_agent_key)
                    save_config({"active_agent": active_agent_key, "plan_tier": plan_tier})
                    last_refresh = 0.0
                elif key in ("p", "t"):
                    plan_tier = get_next_plan(plan_tier, active_agent_key)
                    save_config({"plan_tier": plan_tier})
                    last_refresh = 0.0
                elif key == "m":
                    current_pricing_idx = (current_pricing_idx + 1) % len(PRICING_KEYS)
                    save_config({"pricing_model": PRICING_KEYS[current_pricing_idx]})
                    last_refresh = 0.0
                elif key == "b":
                    show_full_benchmarks = not show_full_benchmarks
                    save_config({"show_benchmarks": show_full_benchmarks})
                    last_refresh = 0.0
                elif key == "r":
                    last_refresh = 0.0

                if now - last_refresh >= args.rate:
                    telemetry = adapter.get_session_telemetry()
                    sys_metrics = get_system_telemetry()

                    dashboard = build_dashboard(
                        telemetry,
                        sys_metrics,
                        active_agent_key,
                        PRICING_KEYS[current_pricing_idx],
                        plan_tier_key=plan_tier,
                        show_full_benchmarks=show_full_benchmarks,
                        console_height=console.size.height
                    )
                    live.update(dashboard, refresh=True)
                    last_refresh = now

                time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        restore_keyboard()
        console.print("[bold #00f3ff]:: toktopus monitor stopped. Goodbye! ::[/bold #00f3ff]")

if __name__ == "__main__":
    main()
