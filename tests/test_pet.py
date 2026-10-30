import unittest

from rich.panel import Panel

from toktopus.core.pet import CyberPet, get_cyber_pet


class TestCyberPet(unittest.TestCase):
    def setUp(self):
        self.pet = CyberPet("TestOcto")

    def test_initialization(self):
        self.assertEqual(self.pet.name, "TestOcto")
        self.assertEqual(self.pet.level, 1)
        self.assertGreaterEqual(self.pet.fuel, 50)
        self.assertGreaterEqual(self.pet.happiness, 50)
        self.assertEqual(self.pet.state, "idle")

    def test_xp_and_level_up(self):
        self.pet.add_xp(50)
        self.assertEqual(self.pet.level, 1)
        self.assertEqual(self.pet.xp, 50)


        self.pet.add_xp(60)
        self.assertEqual(self.pet.level, 2)
        self.assertEqual(self.pet.xp, 10)
        self.assertIn("LEVEL UP", self.pet.current_quip)

    def test_feed_action(self):
        self.pet.fuel = 40
        self.pet.happiness = 50
        msg = self.pet.feed()
        self.assertIn("Fed", msg)
        self.assertGreater(self.pet.fuel, 40)
        self.assertGreater(self.pet.happiness, 50)
        self.assertEqual(self.pet.state, "eating")
        self.assertGreater(self.pet.action_timer, 0)

    def test_pet_action(self):
        self.pet.happiness = 60
        msg = self.pet.pet()
        self.assertIn("Pet", msg)
        self.assertEqual(self.pet.happiness, 85)
        self.assertEqual(self.pet.state, "pet")
        self.assertGreater(self.pet.action_timer, 0)

    def test_autonomous_coding_tick(self):

        self.pet.tick(is_active=True, tokens_per_sec=120, cache_eff=50.0, current_ctx=20000, total_tokens=50000)
        self.assertEqual(self.pet.state, "coding")
        sprite = self.pet.get_current_sprite()
        self.assertIsInstance(sprite, list)
        self.assertGreater(len(sprite), 2)

    def test_autonomous_cache_high_tick(self):

        self.pet.tick(is_active=False, tokens_per_sec=0, cache_eff=92.0, current_ctx=50000, total_tokens=100000)
        self.assertEqual(self.pet.state, "cache_high")
        sprite = self.pet.get_current_sprite()

        self.assertTrue(any("B )" in line for line in sprite))

    def test_autonomous_hungry_tick(self):
        self.pet.fuel = 15
        self.pet.tick(is_active=False, tokens_per_sec=0, cache_eff=40.0, current_ctx=1000, total_tokens=1000)
        self.assertEqual(self.pet.state, "hungry")

    def test_render_widget(self):
        panel = self.pet.render_widget(width=34)
        self.assertIsInstance(panel, Panel)
        self.assertIn("TOKTO", str(panel.title))

    def test_global_pet_singleton(self):
        p1 = get_cyber_pet()
        p2 = get_cyber_pet()
        self.assertIs(p1, p2)

if __name__ == "__main__":
    unittest.main()
