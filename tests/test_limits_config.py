import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from toktopus.core import config
from toktopus.core.config import get_default_plan_for_agent, load_config, save_config
from toktopus.core.limits import (
    TIER_LIMITS,
    auto_detect_plan,
    estimate_account_limits,
    get_next_plan,
    normalize_plan_key,
)


class TestLimitsAndConfig(unittest.TestCase):
    def test_google_ai_pro_plan_registered(self):
        self.assertIn("google-ai-pro", TIER_LIMITS)
        pro = TIER_LIMITS["google-ai-pro"]
        self.assertEqual(pro["tier_name"], "Google AI Pro Plan")
        self.assertEqual(pro["max_context"], 2_000_000)
        self.assertEqual(pro["max_tpm"], 4_000_000)
        self.assertEqual(pro["max_rpm"], 360)
        self.assertTrue(pro["is_subscription"])

    def test_plan_aliases(self):
        self.assertEqual(normalize_plan_key("pro"), "google-ai-pro")
        self.assertEqual(normalize_plan_key("gemini-pro"), "google-ai-pro")
        self.assertEqual(normalize_plan_key("payg"), "gemini-payg")
        self.assertEqual(normalize_plan_key("free"), "gemini-free")
        self.assertEqual(normalize_plan_key("claude", "claude"), "claude-pro")
        self.assertEqual(normalize_plan_key("opencode", "opencode"), "opencode-zen")
        self.assertEqual(normalize_plan_key("cursor", "cursor"), "cursor-pro")

    def test_switching_agent_normalizes_to_valid_plan(self):

        claude_plan = normalize_plan_key("google-ai-pro", agent_key="claude")
        self.assertEqual(claude_plan, "claude-pro")


        cursor_plan = normalize_plan_key("google-ai-pro", agent_key="cursor")
        self.assertEqual(cursor_plan, "cursor-pro")


        opencode_plan = normalize_plan_key("claude-pro", agent_key="opencode")
        self.assertEqual(opencode_plan, "opencode-zen")

    def test_estimate_limits_google_ai_pro(self):
        res = estimate_account_limits(
            agent_key="antigravity",
            recent_tokens=50_000,
            recent_requests=2,
            tier_override="google-ai-pro"
        )
        self.assertEqual(res["tier_name"], "Google AI Pro Plan")
        self.assertEqual(res["plan_badge"], "[PRO PLAN]")
        self.assertEqual(res["max_context"], 2_000_000)
        self.assertEqual(res["max_tpm"], 4_000_000)
        self.assertEqual(res["status"], "SAFE")
        self.assertGreater(res["tpm_remaining"], 3_900_000)

    def test_plan_cycling(self):
        nxt = get_next_plan("google-ai-pro", "antigravity")
        self.assertEqual(nxt, "gemini-payg")
        nxt2 = get_next_plan("gemini-payg", "antigravity")
        self.assertEqual(nxt2, "gemini-free")
        nxt3 = get_next_plan("gemini-free", "antigravity")
        self.assertEqual(nxt3, "google-ai-pro")

    def test_agent_default_plans(self):
        self.assertEqual(get_default_plan_for_agent("antigravity"), "google-ai-pro")
        self.assertEqual(get_default_plan_for_agent("claude"), "claude-pro")
        self.assertEqual(get_default_plan_for_agent("opencode"), "opencode-zen")
        self.assertEqual(get_default_plan_for_agent("cursor"), "cursor-pro")
        self.assertEqual(get_default_plan_for_agent("codex"), "codex-pro")
        self.assertEqual(get_default_plan_for_agent("pi"), "pi-pro")

    def test_auto_detect_plan(self):
        self.assertEqual(auto_detect_plan("antigravity"), "google-ai-pro")
        self.assertEqual(auto_detect_plan("claude"), "claude-pro")
        self.assertEqual(auto_detect_plan("opencode"), "opencode-zen")
        self.assertEqual(auto_detect_plan("cursor"), "cursor-pro")
        self.assertEqual(auto_detect_plan("codex"), "codex-pro")
        self.assertEqual(auto_detect_plan("pi"), "pi-pro")

    def test_config_save_and_load(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(config, "CONFIG_DIR", root), patch.object(config, "CONFIG_FILE", root / "config.json"):
                self.assertTrue(save_config({"test_key": "test_val"}))
                cfg = load_config()
                self.assertIn("plan_tier", cfg)
                self.assertEqual(cfg.get("test_key"), "test_val")

if __name__ == "__main__":
    unittest.main()
