import unittest
from toktopus.game import SpaceImpactGame

class TestSpaceImpactGame(unittest.TestCase):
    def setUp(self):
        self.game = SpaceImpactGame(width=60, height=14)

    def test_game_initialization(self):
        self.assertEqual(self.game.width, 60)
        self.assertEqual(self.game.height, 14)
        self.assertEqual(self.game.player_lives, 3)
        self.assertEqual(self.game.player_hp, 100)
        self.assertEqual(self.game.score, 0)
        self.assertEqual(self.game.wave, 1)
        self.assertFalse(self.game.game_over)
        self.assertFalse(self.game.paused)

    def test_player_movement_bounds(self):
        # Move up
        orig_y = self.game.player_y
        self.game.handle_input("up")
        self.assertEqual(self.game.player_y, max(1, orig_y - 1))

        # Move down
        self.game.handle_input("down")
        self.assertEqual(self.game.player_y, orig_y)

        # Move right
        orig_x = self.game.player_x
        self.game.handle_input("right")
        self.assertEqual(self.game.player_x, orig_x + 1)

        # Move left
        self.game.handle_input("left")
        self.assertEqual(self.game.player_x, orig_x)

    def test_fire_laser(self):
        self.assertEqual(len(self.game.lasers), 0)
        self.game.handle_input("space")
        self.assertEqual(len(self.game.lasers), 1)
        laser = self.game.lasers[0]
        self.assertEqual(laser["x"], self.game.player_x + 2)
        self.assertEqual(laser["y"], self.game.player_y)

    def test_laser_movement_and_culling(self):
        self.game.handle_input("space")
        self.assertEqual(len(self.game.lasers), 1)
        # Advance ticks until laser reaches screen edge
        for _ in range(40):
            self.game.update()
        self.assertEqual(len(self.game.lasers), 0)

    def test_enemy_spawning(self):
        self.assertEqual(len(self.game.enemies), 0)
        for _ in range(30):
            self.game.spawn_entities()
        self.assertGreater(len(self.game.enemies), 0)

    def test_laser_hits_enemy(self):
        # Place enemy directly in front of player
        self.game.enemies.append({
            "x": self.game.player_x + 4,
            "y": self.game.player_y,
            "type": "scout",
            "sprite": "<x>",
            "hp": 1,
            "max_hp": 1,
            "speed": 0,
            "points": 15,
            "color": "green"
        })
        self.game.handle_input("space")
        # Update simulation: laser advances by 2 each tick
        self.game.update()
        self.game.update()
        # Enemy should be destroyed and score awarded
        self.assertEqual(self.game.score, 15)
        self.assertEqual(len(self.game.enemies), 0)

    def test_player_damage_and_lives(self):
        self.game.take_player_damage(50)
        self.assertEqual(self.game.player_hp, 50)
        self.assertEqual(self.game.player_lives, 3)

        # Lethal damage takes one life
        self.game.take_player_damage(60)
        self.assertEqual(self.game.player_lives, 2)
        self.assertEqual(self.game.player_hp, 100)

        # Deplete all lives
        self.game.take_player_damage(100)
        self.game.take_player_damage(100)
        self.assertTrue(self.game.game_over)
        self.assertEqual(self.game.player_lives, 0)

    def test_pause_and_reset(self):
        self.game.handle_input("p")
        self.assertTrue(self.game.paused)
        self.game.handle_input("p")
        self.assertFalse(self.game.paused)

        self.game.score = 500
        self.game.game_over = True
        self.game.handle_input("r")
        self.assertFalse(self.game.game_over)
        self.assertEqual(self.game.score, 0)

    def test_render_frame_contains_hud_and_borders(self):
        frame = self.game.render_frame()
        self.assertIn("SCORE:", frame)
        self.assertIn("LIVES:", frame)
        self.assertIn("HP:", frame)
        self.assertIn("WAVE:", frame)
        lines = frame.splitlines()
        self.assertGreaterEqual(len(lines), self.game.height)

    def test_game_over_screen_rendering(self):
        self.game.game_over = True
        frame = self.game.render_frame()
        self.assertIn("GAME OVER", frame)
        self.assertIn("FINAL SCORE:", frame)

if __name__ == "__main__":
    unittest.main()
