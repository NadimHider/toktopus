import os
import sys
import time
import json
import argparse
from typing import Optional
from rich.console import Console
from rich.live import Live
from rich.table import Table

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
from toktopus.core.pricing import PRICING_TABLE, calculate_costs, resolve_pricing_model
from toktopus.core.benchmarks import get_benchmarks, get_benchmarks_last_updated
from toktopus.core.limits import normalize_plan_key, auto_detect_plan, get_next_plan, estimate_account_limits
from toktopus.core.config import load_config, save_config
from toktopus.core.skills import (
    list_installed_skills,
    get_skill,
    modify_skill,
    copy_skill
)
from toktopus.game import run_space_impact
from toktopus.core.pet import get_cyber_pet, run_pet_lounge

console = Console(theme=THEME_CONFIG)

PRICING_KEYS = list(PRICING_TABLE.keys())

def interactive_edit_skill(active_agent_key: str):
    console.clear()
    skills = list_installed_skills(active_agent_key)
    if not skills:
        skills = list_installed_skills()

    console.print(f"[bold #00ff88]:: TOKTOPUS : Interactive Skill Editor ({active_agent_key.upper()}) ::[/bold #00ff88]")
    if skills:
        console.print("[dim]Installed skills:[/dim]")
        for idx, s in enumerate(skills[:10], 1):
            console.print(f"  [bold #00f3ff][{idx}][/bold #00f3ff] [bold white]{s['name']}[/bold white] [dim]({s['agent']})[/dim]")

    console.print("\n[bold white]Enter skill name or number to edit (or press Enter to cancel):[/bold white]")
    try:
        choice = input("> ").strip()
    except Exception:
        return

    if not choice:
        return

    target_skill_name = choice
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(skills):
            target_skill_name = skills[idx]["name"]

    skill_info = get_skill(target_skill_name, active_agent_key)
    if not skill_info:
        console.print(f"[bold #ff3366]Error: Skill '{target_skill_name}' not found.[/bold #ff3366]")
        time.sleep(1.5)
        return

    console.print(f"\n[bold #00f3ff]Editing skill: {skill_info['name']} ({skill_info['skill_file']})[/bold #00f3ff]")
    console.print("[dim]Choose mode: [1] Append instructions  [2] Replace entire instructions[/dim]")
    try:
        mode_choice = input("Mode [1]: ").strip()
        mode = "replace" if mode_choice == "2" else "append"
        console.print(f"\n[bold white]Enter instructions to {mode} (or leave empty to cancel):[/bold white]")
        instruction_text = input("> ").strip()
    except Exception:
        return

    if not instruction_text:
        console.print("[dim]Modification cancelled.[/dim]")
        time.sleep(1.0)
        return

    success = modify_skill(
        skill_name=skill_info["name"],
        instruction_delta=instruction_text,
        agent_key=active_agent_key,
        mode=mode
    )
    if success:
        console.print(f"[bold #00ff88]:: Successfully modified skill '{skill_info['name']}'! ::[/bold #00ff88]")
    else:
        console.print(f"[bold #ff3366]Error: Failed to modify skill '{skill_info['name']}'.[/bold #ff3366]")
    time.sleep(1.5)

def print_benchmarks_table():
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

def print_skills_table(agent_key: Optional[str] = None):
    skills = list_installed_skills(agent_key)
    title_suffix = f" for {agent_key.upper()}" if agent_key else " across all Agents"
    table = Table(title=f":: TOKTOPUS : Installed Agent Skills Vault ({len(skills)} skills{title_suffix}) ::", border_style="#00ff88")
    table.add_column("Agent", style="bold #00f3ff", no_wrap=True)
    table.add_column("Skill Name", style="bold white", no_wrap=True)
    table.add_column("Description", style="dim")
    table.add_column("File Size", justify="right", style="white")

    for s in skills:
        size_str = f"{s['size_bytes']:,} B" if s['size_bytes'] > 0 else "empty"
        table.add_row(
            s["agent"],
            s["name"],
            s["description"][:65] if s["description"] else "No description",
            size_str
        )

    console.print(table)

def export_telemetry_snapshot(export_path: str, telemetry: dict, sys_metrics: dict, agent_key: str, plan_tier: str, pricing_key: str):
    in_tok = telemetry.get("input_tokens", 0)
    out_tok = telemetry.get("output_tokens", 0)
    cache_tok = telemetry.get("cache_read_tokens", 0)
    reason_tok = telemetry.get("reasoning_tokens", 0)
    cache_write_tok = telemetry.get("cache_creation_tokens", 0) or telemetry.get("cache_write_tokens", 0)
    current_ctx = telemetry.get("current_context_tokens", 0)
    elapsed_sec = telemetry.get("session_elapsed_sec", 0.0)
    recent_steps = telemetry.get("recent_steps", [])

    effective_pricing = resolve_pricing_model(telemetry.get("model_name"), agent_key, pricing_key)
    costs = calculate_costs(
        input_tokens=in_tok,
        output_tokens=out_tok,
        cache_read_tokens=cache_tok,
        model_key=effective_pricing,
        reasoning_tokens=reason_tok,
        cache_write_tokens=cache_write_tok,
        step_count=len(recent_steps) if recent_steps else 1,
        elapsed_sec=elapsed_sec
    )

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
            "session_elapsed_sec": elapsed_sec
        },
        "tokens": {
            "current_context": current_ctx,
            "max_context": limits.get("max_context", 2_000_000),
            "input": in_tok,
            "output": out_tok,
            "cache_read": cache_tok,
            "cache_write": cache_write_tok,
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
        choices=["antigravity", "claude", "opencode", "cursor", "codex", "pi", "auto"],
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
        "--game", "--space-impact",
        dest="run_game",
        action="store_true",
        help="Play the Space Impact terminal arcade game and exit"
    )
    parser.add_argument(
        "--pet", "--pet-lounge",
        dest="run_pet",
        action="store_true",
        help="Launch the interactive Tokto Pet Lounge habitat and exit"
    )
    parser.add_argument(
        "--skills", "--list-skills",
        dest="list_skills",
        action="store_true",
        help="List installed agent skills across coding harnesses and exit"
    )
    parser.add_argument(
        "--get-skill",
        metavar="NAME",
        help="Inspect and print the contents of a specific skill"
    )
    parser.add_argument(
        "--modify-skill",
        metavar="NAME",
        help="Modify or append instructions to an existing installed skill"
    )
    parser.add_argument(
        "--instruction",
        metavar="TEXT",
        help="Instruction content to append or apply when modifying a skill"
    )
    parser.add_argument(
        "--mode",
        choices=["append", "prepend", "replace"],
        default="append",
        help="Modification mode when editing a skill (default: append)"
    )
    parser.add_argument(
        "--copy-skill",
        metavar="NAME",
        help="Copy an installed skill to another agent harness"
    )
    parser.add_argument(
        "--to-agent",
        choices=["antigravity", "claude", "opencode", "cursor", "codex", "pi"],
        help="Target agent harness when copying a skill"
    )
    parser.add_argument(
        "--rate", "-r",
        type=float,
        default=float(saved_cfg.get("refresh_rate", 0.3)),
        help="Refresh interval in seconds (default: 0.3)"
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

    if args.run_game:
        run_space_impact(standalone=True)
        sys.exit(0)

    if args.run_pet:
        run_pet_lounge()
        sys.exit(0)

    if args.benchmarks:
        print_benchmarks_table()
        sys.exit(0)

    if args.list_skills:
        target_agent = None if args.agent == "auto" else args.agent
        print_skills_table(target_agent)
        sys.exit(0)

    if args.get_skill:
        target_agent = None if args.agent == "auto" else args.agent
        skill_data = get_skill(args.get_skill, target_agent)
        if skill_data:
            console.print(f"[bold #00f3ff]:: SKILL: {skill_data['name']} (Agent: {skill_data['agent']}) ::[/bold #00f3ff]")
            console.print(f"[dim]File: {skill_data['skill_file']}[/dim]")
            if skill_data.get("description"):
                console.print(f"[bold #00ff88]Description:[/bold #00ff88] {skill_data['description']}")
            console.print("\n[bold white]Instructions:[/bold white]")
            console.print(skill_data["instructions"])
        else:
            console.print(f"[bold #ff3366]Error: Skill '{args.get_skill}' not found.[/bold #ff3366]")
        sys.exit(0)

    if args.modify_skill:
        if not args.instruction:
            console.print("[bold #ff3366]Error: Please provide --instruction text to modify the skill.[/bold #ff3366]")
            sys.exit(1)
        target_agent = None if args.agent == "auto" else args.agent
        success = modify_skill(
            skill_name=args.modify_skill,
            instruction_delta=args.instruction,
            agent_key=target_agent,
            mode=args.mode
        )
        if success:
            console.print(f"[bold #00ff88]:: Successfully modified skill '{args.modify_skill}' (mode: {args.mode}) ::[/bold #00ff88]")
        else:
            console.print(f"[bold #ff3366]Error: Failed to modify skill '{args.modify_skill}'. Skill not found.[/bold #ff3366]")
        sys.exit(0)

    if args.copy_skill:
        if not args.to_agent:
            console.print("[bold #ff3366]Error: Please specify target agent harness with --to-agent.[/bold #ff3366]")
            sys.exit(1)
        src_agent = "antigravity" if args.agent == "auto" else args.agent
        success = copy_skill(args.copy_skill, src_agent, args.to_agent)
        if success:
            console.print(f"[bold #00ff88]:: Successfully copied skill '{args.copy_skill}' to {args.to_agent} ::[/bold #00ff88]")
        else:
            console.print(f"[bold #ff3366]Error: Failed to copy skill '{args.copy_skill}'.[/bold #ff3366]")
        sys.exit(0)

    if args.agent == "auto":
        active_agent_key = auto_detect_active_agent()
    else:
        active_agent_key = args.agent

    if args.plan:
        plan_tier = normalize_plan_key(args.plan, active_agent_key)
        save_config({"plan_tier": plan_tier})
    else:
        plan_tier = auto_detect_plan(active_agent_key)

    saved_pricing = saved_cfg.get("pricing_model", "gemini-3.8-flash")
    current_pricing_idx = PRICING_KEYS.index(saved_pricing) if saved_pricing in PRICING_KEYS else 0
    show_full_benchmarks = bool(saved_cfg.get("show_benchmarks", False))
    show_skills_expanded = False

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
            show_skills_expanded=False,
            console_height=console.size.height,
            console_width=console.size.width
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
                    plan_tier = auto_detect_plan(active_agent_key)
                    save_config({"active_agent": active_agent_key, "plan_tier": plan_tier})
                    last_refresh = 0.0
                elif key == "p":
                    plan_tier = get_next_plan(plan_tier, active_agent_key)
                    save_config({"plan_tier": plan_tier})
                    last_refresh = 0.0
                elif key == "f":
                    get_cyber_pet().feed()
                    last_refresh = 0.0
                elif key == "t":
                    get_cyber_pet().pet()
                    last_refresh = 0.0
                elif key == "o":
                    restore_keyboard()
                    run_pet_lounge()
                    init_keyboard()
                    last_refresh = 0.0
                elif key == "m":
                    current_pricing_idx = (current_pricing_idx + 1) % len(PRICING_KEYS)
                    save_config({"pricing_model": PRICING_KEYS[current_pricing_idx]})
                    last_refresh = 0.0
                elif key == "b":
                    show_full_benchmarks = not show_full_benchmarks
                    save_config({"show_benchmarks": show_full_benchmarks})
                    last_refresh = 0.0
                elif key == "g":
                    # Launch Space Impact Minigame
                    restore_keyboard()
                    run_space_impact(standalone=False)
                    init_keyboard()
                    last_refresh = 0.0
                elif key == "s":
                    # Toggle collapsible skill vault
                    show_skills_expanded = not show_skills_expanded
                    last_refresh = 0.0
                elif key == "e":
                    # In-place interactive skill editor
                    restore_keyboard()
                    interactive_edit_skill(active_agent_key)
                    init_keyboard()
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
                        show_skills_expanded=show_skills_expanded,
                        console_height=console.size.height,
                        console_width=console.size.width
                    )
                    live.update(dashboard, refresh=True)
                    last_refresh = now

                time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        restore_keyboard()
        console.print("[bold #00f3ff]:: toktopus monitor stopped. Goodbye! ::[/bold #00f3ff]")

if __name__ == "__main__":
    main()
