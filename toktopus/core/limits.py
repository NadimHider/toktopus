from typing import Dict, Any

TIER_LIMITS: Dict[str, Dict[str, Any]] = {
    "gemini-free": {
        "tier_name": "Free Tier",
        "max_rpm": 15,
        "max_tpm": 1_000_000,
        "max_rpd": 1_500,
    },
    "gemini-payg": {
        "tier_name": "Pay-As-You-Go (Tier 1)",
        "max_rpm": 1_000,
        "max_tpm": 4_000_000,
        "max_rpd": 50_000,
    },
    "claude-tier1": {
        "tier_name": "Anthropic Tier 1",
        "max_rpm": 50,
        "max_tpm": 40_000,
        "max_rpd": 5_000,
    },
    "claude-tier2": {
        "tier_name": "Anthropic Tier 2+",
        "max_rpm": 1_000,
        "max_tpm": 400_000,
        "max_rpd": 50_000,
    },
    "opencode-zen": {
        "tier_name": "OpenCode Zen Pool",
        "max_rpm": 60,
        "max_tpm": 2_000_000,
        "max_rpd": 10_000,
    }
}

def estimate_account_limits(
    agent_key: str,
    recent_tokens: int,
    recent_requests: int = 1,
    tier_override: str = "gemini-free"
) -> Dict[str, Any]:
    tier_key = tier_override
    if agent_key == "claude":
        tier_key = "claude-tier1"
    elif agent_key == "opencode":
        tier_key = "opencode-zen"

    limits = TIER_LIMITS.get(tier_key, TIER_LIMITS["gemini-free"])
    
    tpm_used = min(recent_tokens, limits["max_tpm"])
    tpm_pct = round((tpm_used / limits["max_tpm"]) * 100, 1)

    rpm_used = min(recent_requests, limits["max_rpm"])
    rpm_pct = round((rpm_used / limits["max_rpm"]) * 100, 1)

    status = "SAFE"
    if tpm_pct > 80.0 or rpm_pct > 80.0:
        status = "CRITICAL"
    elif tpm_pct > 60.0 or rpm_pct > 60.0:
        status = "WARN"

    return {
        "tier_name": limits["tier_name"],
        "tpm_used": tpm_used,
        "max_tpm": limits["max_tpm"],
        "tpm_pct": tpm_pct,
        "rpm_used": rpm_used,
        "max_rpm": limits["max_rpm"],
        "rpm_pct": rpm_pct,
        "max_rpd": limits["max_rpd"],
        "status": status
    }
