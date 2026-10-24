from typing import List

BRAILLE_LEVELS = [" ", "⡀", "⣀", "⠤", "⠶", "⠒", "⠊", "⠉", "⠑"]

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

def relative_benchmark_bar(score: float, max_score: float = 1600.0, width: int = 12) -> str:
    pct = min(1.0, max(0.0, score / max_score))
    filled = int(pct * width)
    empty = width - filled
    return f"[#00f3ff]{'█' * filled}[/#00f3ff][dim]{'░' * empty}[/dim]"
