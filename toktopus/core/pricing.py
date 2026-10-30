from typing import Any, Dict, Optional

PRICING_TABLE: Dict[str, Dict[str, Any]] = {
    "gemini-3.8-flash": {
        "name": "Gemini 3.8 Flash",
        "provider": "Google DeepMind",
        "input": 0.10,
        "output": 0.40,
        "cache_read": 0.025,
        "cache_write": 0.10,
        "reasoning": 0.40,
        "context_window": 1_000_000
    },
    "gemini-2-5-pro": {
        "name": "Gemini 2.5 Pro",
        "provider": "Google DeepMind",
        "input": 1.25,
        "output": 5.00,
        "cache_read": 0.3125,
        "cache_write": 1.25,
        "reasoning": 5.00,
        "context_window": 2_000_000
    },
    "claude-3-7-sonnet": {
        "name": "Claude 3.7 Sonnet",
        "provider": "Anthropic",
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
        "cache_write": 3.75,
        "reasoning": 15.00,
        "context_window": 200_000
    },
    "claude-5-5": {
        "name": "Claude 5.5",
        "provider": "Anthropic",
        "input": 2.50,
        "output": 10.00,
        "cache_read": 0.30,
        "cache_write": 3.125,
        "reasoning": 10.00,
        "context_window": 500_000
    },
    "gpt-6-1": {
        "name": "GPT 6.1",
        "provider": "OpenAI",
        "input": 2.00,
        "output": 8.00,
        "cache_read": 0.50,
        "cache_write": 2.00,
        "reasoning": 8.00,
        "context_window": 500_000
    },
    "o3-mini": {
        "name": "OpenAI o3-mini",
        "provider": "OpenAI",
        "input": 1.10,
        "output": 4.40,
        "cache_read": 0.55,
        "cache_write": 1.10,
        "reasoning": 4.40,
        "context_window": 200_000
    },
    "deepseek-r4-1-flash": {
        "name": "DeepSeek R4.1 Flash",
        "provider": "DeepSeek",
        "input": 0.08,
        "output": 0.32,
        "cache_read": 0.015,
        "cache_write": 0.08,
        "reasoning": 0.32,
        "context_window": 256_000
    },
    "deepseek-r1": {
        "name": "DeepSeek-R1",
        "provider": "DeepSeek",
        "input": 0.55,
        "output": 2.19,
        "cache_read": 0.14,
        "cache_write": 0.55,
        "reasoning": 2.19,
        "context_window": 128_000
    },
    "qwen-2-5-coder-32b": {
        "name": "Qwen 2.5 Coder 32B",
        "provider": "Alibaba Cloud",
        "input": 0.20,
        "output": 0.20,
        "cache_read": 0.05,
        "cache_write": 0.20,
        "reasoning": 0.20,
        "context_window": 128_000
    }
}

DEFAULT_MODEL_KEY = "gemini-3.8-flash"

def resolve_pricing_model(
    detected_model: Optional[str] = None,
    agent_key: str = "antigravity",
    override_key: Optional[str] = None
) -> str:
    if override_key and override_key in PRICING_TABLE:
        return override_key

    raw = (detected_model or "").lower()

    if "gemini" in raw:
        if "pro" in raw or "2.5" in raw or "2-5" in raw:
            return "gemini-2-5-pro"
        return "gemini-3.8-flash"

    if "claude" in raw or "sonnet" in raw or "opus" in raw:
        if "5.5" in raw or "5-5" in raw:
            return "claude-5-5"
        return "claude-3-7-sonnet"

    if "o3" in raw:
        return "o3-mini"

    if "gpt" in raw or "codex" in raw:
        if "6.1" in raw or "6-1" in raw or "sol" in raw:
            return "gpt-6-1"
        return "o3-mini"

    if "deepseek" in raw:
        if "r1" in raw:
            return "deepseek-r1"
        return "deepseek-r4-1-flash"

    if "qwen" in raw:
        return "qwen-2-5-coder-32b"


    agent_clean = (agent_key or "").lower()
    if agent_clean == "claude" or agent_clean == "cursor":
        return "claude-3-7-sonnet"
    elif agent_clean == "opencode":
        return "deepseek-r4-1-flash"
    elif agent_clean == "codex":
        return "o3-mini"

    return DEFAULT_MODEL_KEY

def calculate_costs(
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    model_key: str = DEFAULT_MODEL_KEY,
    reasoning_tokens: int = 0,
    cache_write_tokens: int = 0,
    step_count: int = 0,
    elapsed_sec: float = 0.0
) -> Dict[str, Any]:
    cfg = PRICING_TABLE.get(model_key, PRICING_TABLE[DEFAULT_MODEL_KEY])

    rate_in = cfg["input"] / 1_000_000.0
    rate_out = cfg["output"] / 1_000_000.0
    rate_cache_read = cfg["cache_read"] / 1_000_000.0
    rate_cache_write = cfg.get("cache_write", cfg["input"]) / 1_000_000.0
    rate_reasoning = cfg.get("reasoning", cfg["output"]) / 1_000_000.0

    cost_in = input_tokens * rate_in
    cost_out = output_tokens * rate_out
    cost_cache_read = cache_read_tokens * rate_cache_read
    cost_cache_write = cache_write_tokens * rate_cache_write
    cost_reasoning = reasoning_tokens * rate_reasoning

    cost_spent = cost_in + cost_out + cost_cache_read + cost_cache_write + cost_reasoning


    cost_without_cache = ((input_tokens + cache_read_tokens) * rate_in) + (output_tokens * rate_out) + (reasoning_tokens * rate_reasoning)
    cost_saved = max(0.0, cost_without_cache - cost_spent)
    savings_pct = (cost_saved / cost_without_cache * 100.0) if cost_without_cache > 0 else 0.0

    cost_per_step = (cost_spent / step_count) if step_count > 0 else 0.0
    burn_hourly = (cost_spent / elapsed_sec * 3600.0) if elapsed_sec > 5.0 else 0.0
    proj_1k_steps = cost_per_step * 1000.0 if cost_per_step > 0 else 0.0

    return {
        "cost_spent_usd": round(cost_spent, 4),
        "cost_saved_usd": round(cost_saved, 4),
        "cost_without_cache_usd": round(cost_without_cache, 4),
        "savings_percent": round(savings_pct, 1),
        "cost_input_usd": round(cost_in, 4),
        "cost_output_usd": round(cost_out, 4),
        "cost_cache_read_usd": round(cost_cache_read, 4),
        "cost_cache_write_usd": round(cost_cache_write, 4),
        "cost_reasoning_usd": round(cost_reasoning, 4),
        "cost_per_step_usd": round(cost_per_step, 4),
        "burn_rate_hourly_usd": round(burn_hourly, 4),
        "projected_1k_steps_usd": round(proj_1k_steps, 2),
        "rate_in": cfg["input"],
        "rate_out": cfg["output"],
        "rate_cache": cfg["cache_read"],
        "rate_cache_write": cfg.get("cache_write", cfg["input"]),
        "model_name": cfg["name"],
        "provider": cfg["provider"]
    }
