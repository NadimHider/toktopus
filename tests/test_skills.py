import unittest
from toktopus.core.skills import count_skills_and_plugins

class TestSkills(unittest.TestCase):
    def test_count_skills_and_plugins_antigravity(self):
        res = count_skills_and_plugins("antigravity")
        self.assertIn("skills", res)
        self.assertIn("plugins", res)
        self.assertIsInstance(res["skills"], int)
        self.assertIsInstance(res["plugins"], int)
        self.assertGreaterEqual(res["skills"], 0)

    def test_count_skills_and_plugins_claude(self):
        res = count_skills_and_plugins("claude")
        self.assertIn("skills", res)
        self.assertIn("plugins", res)
        self.assertIsInstance(res["skills"], int)

    def test_count_skills_and_plugins_fallback(self):
        res = count_skills_and_plugins("nonexistent_agent")
        self.assertIn("skills", res)
        self.assertIn("plugins", res)

if __name__ == "__main__":
    unittest.main()
