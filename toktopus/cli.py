import sys
import time
import argparse
from rich.console import Console
from rich.live import Live

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from toktopus.ui.theme import THEME_CONFIG
from toktopus.ui.layout import build_dashboard
from toktopus.adapters import KEY_MAP, get_adapter, auto_detect_active_agent
from toktopus.core.system import get_system_telemetry
from toktopus.core.keyboard import get_pressed_key
from toktopus.core.pricing import PRICING_TABLE
from toktopus.core.benchmarks import get_benchmarks
from toktopus.core.limits import normalize_plan_key, get_next_plan
from toktopus.core.config import load_config, save_config

console = Console(theme=THEME_CONFIG)

PRICING_KEYS = list(PRICING_TABLE.keys())

def print_benchmarks_table():
    from rich.table import Table
    from toktopus.ui.charts import relative_benchmark_bar

    table = Table(title=":: TOKTOPUS : AI Coding Model Benchmark Index ::", border_style="#ffe600")
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
        "--version", "-v",
        action="version",
        version="toktopus v1.1.0"
    )

    args = parser.parse_args()

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

    if args.once:
        dashboard = build_dashboard(
            telemetry,
            sys_metrics,
            active_agent_key,
            PRICING_KEYS[current_pricing_idx],
            plan_tier_key=plan_tier,
            show_full_benchmarks=False
        )
        console.print(dashboard)
        sys.exit(0)

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
                        show_full_benchmarks=show_full_benchmarks
                    )
                    live.update(dashboard, refresh=True)
                    last_refresh = now

                time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        console.print("[bold #00f3ff]:: toktopus monitor stopped. Goodbye! ::[/bold #00f3ff]")

if __name__ == "__main__":
    main()
