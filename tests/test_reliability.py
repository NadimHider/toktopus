import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from toktopus.core import config
from toktopus.game import SpaceImpactGame


class ReliabilityTests(unittest.TestCase):
    def test_invalid_configuration_falls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps({"refresh_rate": "broken", "active_agent": "invalid"}))
            with patch.object(config, "CONFIG_FILE", path):
                result = config.load_config()
            self.assertEqual(result["refresh_rate"], 0.3)
            self.assertEqual(result["active_agent"], "antigravity")

    def test_atomic_configuration_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(config, "CONFIG_DIR", root), patch.object(config, "CONFIG_FILE", root / "config.json"):
                self.assertTrue(config.save_config({"space_impact_high_score": 600}))
                self.assertEqual(config.load_config()["space_impact_high_score"], 600)
                self.assertEqual(len(list(root.iterdir())), 1)

    def test_boss_threshold_is_not_reused(self):
        game = SpaceImpactGame()
        game.score = 400
        game.tick_count = 101
        game.spawn_entities()
        self.assertTrue(game.boss_active)
        game.boss_active = False
        game.enemies.clear()
        game.spawn_entities()
        self.assertFalse(game.boss_active)
        self.assertEqual(game.next_boss_score, 800)

    def test_simultaneous_lasers_do_not_double_score(self):
        game = SpaceImpactGame()
        game.enemies.append({"x": 7, "y": game.player_y, "type": "scout", "sprite": "<x>", "hp": 1, "speed": 0, "points": 15})
        game.fire_laser()
        game.fire_laser()
        game.update()
        self.assertEqual(game.score, 15)


if __name__ == "__main__":
    unittest.main()
