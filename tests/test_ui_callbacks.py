import sys
import os
import unittest

sys.path.insert(0, os.path.abspath("."))
from arena.game import Game
from arena.board import RED, GREEN, YELLOW, BLUE
from arena.ludo import load_callback, move_callback, reset_callback, model_callback


class TestUICallbacks(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def test_load_callback(self):
        res = load_callback(self.game)
        self.assertEqual(len(res), 9)
        game_obj, svg, msg, red_th, green_th, yellow_th, blue_th, records, ratings = res
        self.assertIn("<svg", svg)
        self.assertTrue(isinstance(msg, str))

    def test_move_callback(self):
        res = move_callback(self.game)
        self.assertEqual(len(res), 9)

    def test_reset_callback(self):
        res = reset_callback(self.game)
        self.assertEqual(len(res), 15)
        self.assertTrue(self.game.stopped)
        self.assertEqual(self.game.board.turns_played, 0)
        self.assertEqual(len(self.game.move_history), 0)

    def test_reset_does_not_auto_restart(self):
        self.game.move()
        self.assertTrue(self.game.board.turns_played > 0 or len(self.game.move_history) > 0)
        res = reset_callback(self.game)
        (
            game_obj, svg, msg, red_th, green_th, yellow_th, blue_th, records, ratings,
            run_btn_up, stop_btn_up, red_dd_up, green_dd_up, yellow_dd_up, blue_dd_up
        ) = res
        self.assertTrue(game_obj.stopped)
        self.assertEqual(game_obj.board.turns_played, 0)
        self.assertIn("<b>Threats:</b> -", red_th)
        self.assertNotIn("<b>Evaluation:</b>", red_th)
        self.assertEqual(run_btn_up.get("interactive"), True)
        self.assertEqual(stop_btn_up.get("interactive"), False)
        self.assertEqual(red_dd_up.get("interactive"), True)
        self.assertEqual(green_dd_up.get("interactive"), True)

    def test_model_callback(self):
        # When game is not running, model switch is allowed
        self.game.is_running = False
        updated_game = model_callback(RED, self.game, "gpt-oss-20b (Groq)")
        self.assertEqual(updated_game.players[RED].model, "gpt-oss-20b (Groq)")

        # When game is running, model switch is blocked
        self.game.is_running = True
        blocked_game = model_callback(RED, self.game, "gemini-2.5-flash")
        self.assertEqual(blocked_game.players[RED].model, "gpt-oss-20b (Groq)")


if __name__ == "__main__":
    unittest.main()
