"""
Model pricing and cost calculation matrix for toktopus.
Prices in USD per 1,000,000 tokens.
"""

from typing import Dict, Any

PRICING_TABLE: Dict[str, Dict[str, Any]] = {
    "gemini-3.8-flash": {
        "name": "Gemini 3.8 Flash",
        "provider": "Google DeepMind",
        "input": 0.10,
        "output": 0.40,
        "cache_read": 0.025,
        "context_window": 200_000
    },
    "gemini-3.5-flash-lite": {
        "name": "Gemini 3.5 Flash-Lite",
        "provider": "Google DeepMind",
        "input": 0.075,
        "output": 0.30,
        "cache_read": 0.01875,
        "context_window": 200_000
    },
    "gemini-3.1-pro": {
        "name": "Gemini 3.1 Pro",
        "provider": "Google DeepMind",
        "input": 1.25,
        "output": 5.00,
        "cache_read": 0.3125,
        "context_window": 2_000_000
    },
    "claude-3-7-sonnet": {
        "name": "Claude 3.7 Sonnet",
        "provider": "Anthropic",
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
        "context_window": 200_000
    },
    "claude-3-5-haiku": {
        "name": "Claude 3.5 Haiku",
        "provider": "Anthropic",
        "input": 0.80,
        "output": 4.00,
        "cache_read": 0.08,
        "context_window": 200_000
    },
    "gpt-4o": {
        "name": "GPT-4o",
        "provider": "OpenAI",
        "input": 2.50,
        "output": 10.00,
        "cache_read": 1.25,
        "context_window": 128_000
    },
    "gpt-5.4-mini": {
        "name": "GPT-5.4 Mini",
        "provider": "OpenAI",
        "input": 0.15,
        "output": 0.60,
        "cache_read": 0.075,
        "context_window": 128_000
    },
    "deepseek-v3": {
        "name": "DeepSeek-V3",
        "provider": "DeepSeek",
        "input": 0.14,
        "output": 0.28,
        "cache_read": 0.014,
        "context_window": 128_000
    },
    "deepseek-r1": {
        "name": "DeepSeek-R1",
        "provider": "DeepSeek",
        "input": 0.55,
        "output": 2.19,
        "cache_read": 0.14,
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
    """Calculate actual cost spent and dollars saved via context caching."""
    cfg = PRICING_TABLE.get(model_key, PRICING_TABLE[DEFAULT_MODEL_KEY])
    
    rate_in = cfg["input"] / 1_000_000.0
    rate_out = cfg["output"] / 1_000_000.0
    rate_cache = cfg["cache_read"] / 1_000_000.0

    cost_spent = (input_tokens * rate_in) + (output_tokens * rate_out) + (cache_read_tokens * rate_cache)
    
    # What it would have cost without cache (cache tokens billed at full input rate)
    cost_without_cache = ((input_tokens + cache_read_tokens) * rate_in) + (output_tokens * rate_out)
    cost_saved = max(0.0, cost_without_cache - cost_spent)

    return {
        "cost_spent_usd": round(cost_spent, 4),
        "cost_saved_usd": round(cost_saved, 4),
        "rate_in": cfg["input"],
        "rate_out": cfg["output"],
        "model_name": cfg["name"]
    }
