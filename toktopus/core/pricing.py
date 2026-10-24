from typing import Dict, Any

PRICING_TABLE: Dict[str, Dict[str, Any]] = {
    "gemini-3.8-flash": {
        "name": "Gemini 3.8 Flash",
        "provider": "Google DeepMind",
        "input": 0.10,
        "output": 0.40,
        "cache_read": 0.025,
        "context_window": 1_000_000
    },
    "gpt-6-1": {
        "name": "GPT 6.1",
        "provider": "OpenAI",
        "input": 2.00,
        "output": 8.00,
        "cache_read": 0.50,
        "context_window": 500_000
    },
    "claude-5-5": {
        "name": "Claude 5.5",
        "provider": "Anthropic",
        "input": 2.50,
        "output": 10.00,
        "cache_read": 0.30,
        "context_window": 500_000
    },
    "deepseek-r4-1-flash": {
        "name": "DeepSeek R4.1 Flash",
        "provider": "DeepSeek",
        "input": 0.08,
        "output": 0.32,
        "cache_read": 0.015,
        "context_window": 256_000
    },
    "claude-3-7-sonnet": {
        "name": "Claude 3.7 Sonnet",
        "provider": "Anthropic",
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
        "context_window": 200_000
    },
    "gemini-2-5-pro": {
        "name": "Gemini 2.5 Pro",
        "provider": "Google DeepMind",
        "input": 1.25,
        "output": 5.00,
        "cache_read": 0.3125,
        "context_window": 2_000_000
    },
    "o3-mini": {
        "name": "OpenAI o3-mini",
        "provider": "OpenAI",
        "input": 1.10,
        "output": 4.40,
        "cache_read": 0.55,
        "context_window": 200_000
    },
    "deepseek-r1": {
        "name": "DeepSeek-R1",
        "provider": "DeepSeek",
        "input": 0.55,
        "output": 2.19,
        "cache_read": 0.14,
        "context_window": 128_000
    },
    "qwen-2-5-coder-32b": {
        "name": "Qwen 2.5 Coder 32B",
        "provider": "Alibaba Cloud",
        "input": 0.20,
        "output": 0.20,
        "cache_read": 0.05,
        "context_window": 128_000
    }
}

DEFAULT_MODEL_KEY = "gemini-3.8-flash"

def calculate_costs(
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int,
    model_key: str = DEFAULT_MODEL_KEY
) -> Dict[str, float]:
    cfg = PRICING_TABLE.get(model_key, PRICING_TABLE[DEFAULT_MODEL_KEY])

    rate_in = cfg["input"] / 1_000_000.0
    rate_out = cfg["output"] / 1_000_000.0
    rate_cache = cfg["cache_read"] / 1_000_000.0

    cost_spent = (input_tokens * rate_in) + (output_tokens * rate_out) + (cache_read_tokens * rate_cache)
    cost_without_cache = ((input_tokens + cache_read_tokens) * rate_in) + (output_tokens * rate_out)
    cost_saved = max(0.0, cost_without_cache - cost_spent)

    return {
        "cost_spent_usd": round(cost_spent, 4),
        "cost_saved_usd": round(cost_saved, 4),
        "rate_in": cfg["input"],
        "rate_out": cfg["output"],
        "model_name": cfg["name"]
    }
