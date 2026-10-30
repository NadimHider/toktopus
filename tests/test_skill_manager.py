import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from toktopus.core.skills import (
    AGENT_SKILL_PATHS,
    _build_frontmatter_text,
    _parse_frontmatter,
    copy_skill,
    create_skill,
    get_skill,
    modify_skill,
)


class TestSkillManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="toktopus_skills_test_")
        self.antigravity_dir = Path(self.temp_dir) / "antigravity_skills"
        self.claude_dir = Path(self.temp_dir) / "claude_skills"
        self.antigravity_dir.mkdir(parents=True, exist_ok=True)
        self.claude_dir.mkdir(parents=True, exist_ok=True)

        self.mock_paths = {
            "antigravity": [self.antigravity_dir],
            "claude": [self.claude_dir],
            "opencode": [],
            "codex": [],
            "cursor": []
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_frontmatter(self):
        raw = "---\nname: my-skill\ndescription: A helpful skill\n---\n# My Skill\nRun steps here."
        fm, body = _parse_frontmatter(raw)
        self.assertEqual(fm.get("name"), "my-skill")
        self.assertEqual(fm.get("description"), "A helpful skill")
        self.assertIn("# My Skill", body)

    def test_parse_frontmatter_without_header(self):
        raw = "# Just Markdown\nNo frontmatter here."
        fm, body = _parse_frontmatter(raw)
        self.assertEqual(fm, {})
        self.assertEqual(body, raw)

    def test_build_frontmatter_text(self):
        fm = {"name": "test-tool", "description": "Quick test"}
        text = _build_frontmatter_text(fm)
        self.assertIn("---", text)
        self.assertIn("name: test-tool", text)
        self.assertIn("description: Quick test", text)

    def test_create_and_get_skill(self):
        with patch.dict(AGENT_SKILL_PATHS, self.mock_paths, clear=False):
            skill_path = create_skill(
                skill_name="code-audit",
                agent_key="antigravity",
                instructions="# Code Audit\nAudit the code systematically.",
                description="Audits codebase"
            )
            self.assertIsNotNone(skill_path)
            self.assertTrue(skill_path.exists())

            info = get_skill("code-audit", agent_key="antigravity")
            self.assertIsNotNone(info)
            self.assertEqual(info["name"], "code-audit")
            self.assertEqual(info["description"], "Audits codebase")
            self.assertIn("Audit the code systematically.", info["instructions"])

    def test_modify_skill_append_with_backup(self):
        with patch.dict(AGENT_SKILL_PATHS, self.mock_paths, clear=False):
            create_skill(
                skill_name="linter-skill",
                agent_key="antigravity",
                instructions="Initial instructions.",
                description="Runs lint"
            )

            success = modify_skill(
                skill_name="linter-skill",
                instruction_delta="Additional strict rule: no unused imports.",
                agent_key="antigravity",
                mode="append",
                backup=True
            )
            self.assertTrue(success)

            updated = get_skill("linter-skill", agent_key="antigravity")
            self.assertIn("Initial instructions.", updated["instructions"])
            self.assertIn("Additional strict rule: no unused imports.", updated["instructions"])


            bak_file = Path(updated["skill_file"]).with_suffix(".md.bak")
            self.assertTrue(bak_file.exists())

    def test_modify_skill_replace_mode(self):
        with patch.dict(AGENT_SKILL_PATHS, self.mock_paths, clear=False):
            create_skill(
                skill_name="formatter-skill",
                agent_key="antigravity",
                instructions="Old formatting rules.",
                description="Formats code"
            )

            success = modify_skill(
                skill_name="formatter-skill",
                instruction_delta="Brand new replacement rules.",
                agent_key="antigravity",
                mode="replace"
            )
            self.assertTrue(success)

            updated = get_skill("formatter-skill", agent_key="antigravity")
            self.assertEqual(updated["instructions"], "Brand new replacement rules.")

    def test_copy_skill_across_agents(self):
        with patch.dict(AGENT_SKILL_PATHS, self.mock_paths, clear=False):
            create_skill(
                skill_name="shared-optimizer",
                agent_key="antigravity",
                instructions="Shared optimization rules across harnesses.",
                description="Cross-agent optimizer"
            )

            copy_success = copy_skill("shared-optimizer", from_agent="antigravity", to_agent="claude")
            self.assertTrue(copy_success)

            claude_skill = get_skill("shared-optimizer", agent_key="claude")
            self.assertIsNotNone(claude_skill)
            self.assertEqual(claude_skill["agent"], "claude")
            self.assertIn("Shared optimization rules", claude_skill["instructions"])

    def test_get_nonexistent_skill_returns_none(self):
        with patch.dict(AGENT_SKILL_PATHS, self.mock_paths, clear=False):
            res = get_skill("skill-that-does-not-exist", agent_key="antigravity")
            self.assertIsNone(res)

    def test_modify_nonexistent_skill_returns_false(self):
        with patch.dict(AGENT_SKILL_PATHS, self.mock_paths, clear=False):
            res = modify_skill("fake-skill", "some delta", agent_key="antigravity")
            self.assertFalse(res)

if __name__ == "__main__":
    unittest.main()
