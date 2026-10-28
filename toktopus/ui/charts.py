from typing import List, Dict, Any

BRAILLE_LEVELS = [" ", "⡀", "⣀", "⠤", "⠶", "⠒", "⠊", "⠉", "⠑"]
SUB_BLOCKS = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]

def format_metric_number(val: float | int) -> str:
    n = float(val)
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    elif n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{int(n)}"

def braille_sparkline(data: List[int], max_width: int = 28) -> str:
    if not data:
        return "⡀" * max_width

    points = data[-max_width:]
    mn, mx = min(points), max(points)

    if mn == mx:
        return "⠤" * len(points)

    result = []
    num_levels = len(BRAILLE_LEVELS) - 1
    for val in points:
        idx = int(((val - mn) / (mx - mn)) * num_levels)
        idx = max(0, min(num_levels, idx))
        result.append(BRAILLE_LEVELS[idx])

    return "".join(result)

def context_gauge(used_tokens: int, max_tokens: int, width: int = 24) -> str:
    if max_tokens <= 0:
        return f"[dim][{'░' * width}] 0.0%[/dim]"

    pct = min(1.0, max(0.0, used_tokens / max_tokens))
    filled_len = int(pct * width)
    empty_len = width - filled_len

    color = "#00ff88"
    if pct > 0.80:
        color = "#ff3366"
    elif pct > 0.55:
        color = "#ffe600"

    bar = f"[{color}]{'█' * filled_len}[/{color}][dim]{'░' * empty_len}[/dim]"
    return f"{bar} {pct * 100:.1f}%"

def quota_gauge(used: int, limit: int, width: int = 16) -> str:
    if limit <= 0:
        return f"[dim][{'░' * width}][/dim]"

    pct = min(1.0, max(0.0, used / limit))
    filled = int(pct * width)
    empty = width - filled

    color = "#00ff88"
    if pct > 0.85:
        color = "#ff3366"
    elif pct > 0.60:
        color = "#ffe600"

    return f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim] {pct * 100:.1f}%"

def cache_efficiency_gauge(efficiency_pct: float, width: int = 20) -> str:
    clamped = min(100.0, max(0.0, efficiency_pct))
    pct = clamped / 100.0
    filled = int(pct * width)
    empty = width - filled

    if clamped >= 80.0:
        color = "#00ff88"
        badge = "OPTIMAL"
    elif clamped >= 60.0:
        color = "#00f3ff"
        badge = "EFFICIENT"
    elif clamped >= 35.0:
        color = "#ffe600"
        badge = "MODERATE"
    else:
        color = "#ff3366"
        badge = "COLD"

    bar = f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim]"
    return f"{bar} [{color}]{clamped:.1f}% [{badge}][/{color}]"

def efficiency_status_badge(efficiency_pct: float) -> str:
    if efficiency_pct >= 85.0:
        return "[bold #00ff88][ELITE CACHE][/bold #00ff88]"
    elif efficiency_pct >= 60.0:
        return "[bold #00f3ff][OPTIMAL][/bold #00f3ff]"
    elif efficiency_pct >= 35.0:
        return "[bold #ffe600][MODERATE][/bold #ffe600]"
    return "[bold #ff3366][COLD MISS][/bold #ff3366]"

def cache_split_bar(cached_tokens: int, fresh_tokens: int, width: int = 24) -> str:
    total = cached_tokens + fresh_tokens
    if total <= 0:
        return f"[dim][{'░' * width}][/dim]"

    cached_len = int((cached_tokens / total) * width)
    fresh_len = width - cached_len

    return (
        f"[#00ff88]{'█' * cached_len}[/#00ff88]"
        f"[#00f3ff]{'█' * fresh_len}[/#00f3ff]"
    )

def cache_trend_sparkline(recent_steps: List[Dict[str, Any]], max_width: int = 20) -> str:
    if not recent_steps:
        return "⠤" * min(5, max_width)

    eff_points = []
    for s in recent_steps[-max_width:]:
        c_tok = s.get("cache_tokens") or s.get("cache_read_tokens") or 0
        in_tok = s.get("input_tokens") or 0
        tot = c_tok + in_tok
        if tot > 0:
            eff = int((c_tok / tot) * 100)
        else:
            eff = 0
        eff_points.append(eff)

    if not eff_points:
        return "⠤" * min(5, max_width)

    return braille_sparkline(eff_points, max_width=len(eff_points))

def cost_burn_bar(cost_usd: float, max_budget_usd: float = 10.0, width: int = 16) -> str:
    budget = max(0.01, max_budget_usd)
    pct = min(1.0, max(0.0, cost_usd / budget))
    filled = int(pct * width)
    empty = width - filled

    color = "#00ff88"
    if pct > 0.80:
        color = "#ff3366"
    elif pct > 0.50:
        color = "#ffe600"

    return f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim]"

def stacked_token_ratio_bar(cache_tokens: int, input_tokens: int, output_tokens: int, width: int = 30) -> str:
    total = cache_tokens + input_tokens + output_tokens
    if total <= 0:
        return f"[dim][{'░' * width}][/dim]"

    cache_len = int((cache_tokens / total) * width)
    in_len = int((input_tokens / total) * width)
    out_len = max(0, width - cache_len - in_len)

    return (
        f"[#00ff88]{'█' * cache_len}[/#00ff88]"
        f"[#00f3ff]{'█' * in_len}[/#00f3ff]"
        f"[#b026ff]{'█' * out_len}[/#b026ff]"
    )

def mini_cpu_gauge(percent: float, width: int = 12) -> str:
    pct = min(1.0, max(0.0, percent / 100.0))
    filled = int(pct * width)
    empty = width - filled

    color = "#00ff88"
    if percent > 85.0:
        color = "#ff3366"
    elif percent > 60.0:
        color = "#ffe600"

    return f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim]"

def large_cache_gauge(efficiency_pct: float, width: int = 28) -> str:
    clamped = min(100.0, max(0.0, efficiency_pct))
    pct = clamped / 100.0
    filled = int(pct * width)
    empty = width - filled

    if clamped >= 85.0:
        color = "#00ff88"
        badge = "ELITE"
    elif clamped >= 60.0:
        color = "#00f3ff"
        badge = "OPTIMAL"
    elif clamped >= 35.0:
        color = "#ffe600"
        badge = "MODERATE"
    else:
        color = "#ff3366"
        badge = "COLD"

    bar = f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim]"
    return f"{bar} [{color}]{clamped:.1f}% [{badge}][/{color}]"

def token_composition_tank(
    cache_tokens: int,
    input_tokens: int,
    output_tokens: int,
    reasoning_tokens: int = 0,
    width: int = 32
) -> str:
    total = cache_tokens + input_tokens + output_tokens + reasoning_tokens
    if total <= 0:
        return f"[dim][{'░' * width}][/dim]"

    c_len = int((cache_tokens / total) * width)
    in_len = int((input_tokens / total) * width)
    out_len = int((output_tokens / total) * width)
    reason_len = max(0, width - c_len - in_len - out_len)

    return (
        f"[#00ff88]{'█' * c_len}[/#00ff88]"
        f"[#00f3ff]{'█' * in_len}[/#00f3ff]"
        f"[#b026ff]{'█' * out_len}[/#b026ff]"
        f"[#ffe600]{'█' * reason_len}[/#ffe600]"
    )

def system_resource_bar(used: float, total: float, width: int = 12) -> str:
    if total <= 0:
        return f"[dim][{'░' * width}][/dim]"
    pct = min(1.0, max(0.0, used / total))
    filled = int(pct * width)
    empty = width - filled
    color = "#00ff88"
    if pct > 0.85:
        color = "#ff3366"
    elif pct > 0.65:
        color = "#ffe600"
    return f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim]"

def relative_benchmark_bar(score: float, max_score: float = 1600.0, width: int = 12) -> str:
    pct = min(1.0, max(0.0, score / max_score))
    filled = int(pct * width)
    empty = width - filled
    return f"[#00f3ff]{'█' * filled}[/#00f3ff][dim]{'░' * empty}[/dim]"
