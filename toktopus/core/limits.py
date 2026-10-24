from typing import Dict, Any, List

TIER_LIMITS: Dict[str, Dict[str, Any]] = {
    "google-ai-pro": {
        "tier_name": "Google AI Pro Plan",
        "plan_badge": "[PRO PLAN]",
        "max_context": 2_000_000,
        "max_rpm": 360,
        "max_tpm": 4_000_000,
        "max_rpd": 50_000,
        "monthly_allowance_usd": 20.00,
        "is_subscription": True,
        "description": "Google AI Pro Plan with Gemini Pro and Advanced models"
    },
    "gemini-payg": {
        "tier_name": "Google AI Pay-As-You-Go",
        "plan_badge": "[TIER 1 PAYG]",
        "max_context": 2_000_000,
        "max_rpm": 1_000,
        "max_tpm": 4_000_000,
        "max_rpd": 100_000,
        "monthly_allowance_usd": 0.00,
        "is_subscription": False,
        "description": "Google Cloud Vertex and AI Studio Pay As You Go"
    },
    "gemini-free": {
        "tier_name": "Google AI Free Tier",
        "plan_badge": "[FREE TIER]",
        "max_context": 1_000_000,
        "max_rpm": 15,
        "max_tpm": 1_000_000,
        "max_rpd": 1_500,
        "monthly_allowance_usd": 0.00,
        "is_subscription": False,
        "description": "Google AI Studio Free Tier"
    },
    "claude-pro": {
        "tier_name": "Claude Pro Plan",
        "plan_badge": "[CLAUDE PRO]",
        "max_context": 200_000,
        "max_rpm": 100,
        "max_tpm": 160_000,
        "max_rpd": 10_000,
        "monthly_allowance_usd": 20.00,
        "is_subscription": True,
        "description": "Claude Pro Web and Code Subscription"
    },
    "claude-tier2": {
        "tier_name": "Anthropic API Tier 2+",
        "plan_badge": "[API TIER 2+]",
        "max_context": 200_000,
        "max_rpm": 1_000,
        "max_tpm": 400_000,
        "max_rpd": 50_000,
        "monthly_allowance_usd": 0.00,
        "is_subscription": False,
        "description": "Anthropic Commercial API Tier 2 and above"
    },
    "opencode-zen": {
        "tier_name": "OpenCode Zen Pool",
        "plan_badge": "[OPENCODE ZEN]",
        "max_context": 1_000_000,
        "max_rpm": 120,
        "max_tpm": 2_000_000,
        "max_rpd": 20_000,
        "monthly_allowance_usd": 0.00,
        "is_subscription": False,
        "description": "OpenCode community and private model routing pool"
    },
    "cursor-pro": {
        "tier_name": "Cursor Pro Plan",
        "plan_badge": "[CURSOR PRO]",
        "max_context": 200_000,
        "max_rpm": 200,
        "max_tpm": 1_000_000,
        "max_rpd": 10_000,
        "monthly_allowance_usd": 20.00,
        "is_subscription": True,
        "description": "Cursor Pro monthly developer subscription"
    }
}

PLAN_ALIASES: Dict[str, str] = {
    "pro": "google-ai-pro",
    "google-pro": "google-ai-pro",
    "google-ai-pro": "google-ai-pro",
    "gemini-pro": "google-ai-pro",
    "payg": "gemini-payg",
    "gemini-payg": "gemini-payg",
    "free": "gemini-free",
    "gemini-free": "gemini-free",
    "claude": "claude-pro",
    "claude-pro": "claude-pro",
    "claude-api": "claude-tier2",
    "claude-tier2": "claude-tier2",
    "opencode": "opencode-zen",
    "opencode-zen": "opencode-zen",
    "cursor": "cursor-pro",
    "cursor-pro": "cursor-pro"
}

AGENT_PLAN_CYCLE: Dict[str, List[str]] = {
    "antigravity": ["google-ai-pro", "gemini-payg", "gemini-free"],
    "claude": ["claude-pro", "claude-tier2"],
    "opencode": ["opencode-zen", "google-ai-pro"],
    "cursor": ["cursor-pro", "claude-pro"]
}

def normalize_plan_key(raw_key: str, agent_key: str = "antigravity") -> str:
    cleaned = (raw_key or "").strip().lower()
    resolved = PLAN_ALIASES.get(cleaned, cleaned)
    valid_cycle = AGENT_PLAN_CYCLE.get(agent_key, list(TIER_LIMITS.keys()))
    if resolved in valid_cycle:
        return resolved

    fallback_map = {
        "antigravity": "google-ai-pro",
        "claude": "claude-pro",
        "opencode": "opencode-zen",
        "cursor": "cursor-pro"
    }
    return fallback_map.get(agent_key, "google-ai-pro")

def get_next_plan(current_plan: str, agent_key: str = "antigravity") -> str:
    cycle = AGENT_PLAN_CYCLE.get(agent_key, list(TIER_LIMITS.keys()))
    norm_cur = normalize_plan_key(current_plan, agent_key)
    if norm_cur in cycle:
        idx = cycle.index(norm_cur)
        return cycle[(idx + 1) % len(cycle)]
    return cycle[0]

def estimate_account_limits(
    agent_key: str,
    recent_tokens: int,
    recent_requests: int = 1,
    tier_override: str = ""
) -> Dict[str, Any]:
    effective_plan = normalize_plan_key(tier_override or "", agent_key)
    limits = TIER_LIMITS.get(effective_plan, TIER_LIMITS["google-ai-pro"])

    tpm_used = min(recent_tokens, limits["max_tpm"])
    tpm_remaining = max(0, limits["max_tpm"] - tpm_used)
    tpm_pct = round((tpm_used / limits["max_tpm"]) * 100, 1)

    rpm_used = min(recent_requests, limits["max_rpm"])
    rpm_remaining = max(0, limits["max_rpm"] - rpm_used)
    rpm_pct = round((rpm_used / limits["max_rpm"]) * 100, 1)

    status = "SAFE"
    if tpm_pct > 80.0 or rpm_pct > 80.0:
        status = "CRITICAL"
    elif tpm_pct > 60.0 or rpm_pct > 60.0:
        status = "WARN"

    return {
        "plan_key": effective_plan,
        "tier_name": limits["tier_name"],
        "plan_badge": limits["plan_badge"],
        "max_context": limits["max_context"],
        "tpm_used": tpm_used,
        "max_tpm": limits["max_tpm"],
        "tpm_remaining": tpm_remaining,
        "tpm_pct": tpm_pct,
        "rpm_used": rpm_used,
        "max_rpm": limits["max_rpm"],
        "rpm_remaining": rpm_remaining,
        "rpm_pct": rpm_pct,
        "max_rpd": limits["max_rpd"],
        "is_subscription": limits.get("is_subscription", False),
        "status": status
    }
