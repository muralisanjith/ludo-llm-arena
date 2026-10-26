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

    def test_wait_with_stop_check(self):
        import time
        from arena.ludo import wait_with_stop_check
        # When game is stopped, wait_with_stop_check returns True immediately without sleeping full duration
        self.game.stopped = True
        t0 = time.time()
        stopped = wait_with_stop_check(self.game, 1.2, step=0.1)
        self.assertTrue(stopped)
        self.assertLess(time.time() - t0, 0.2)

    def test_run_callback_frame_sequencing(self):
        from arena.ludo import run_callback
        # Mock players to avoid real API calls in quick loop test
        for p in self.game.players.values():
            p.process_move = lambda board: board.move(board.legal_moves()[0]) if board.legal_moves() else False

        # Run generator and capture first yield (which must be dice roll frame)
        gen = run_callback(self.game)
        first_frame = next(gen)
        # In first frame, dice must be rolled
        game_out, svg_out, msg_out = first_frame[0], first_frame[1], first_frame[2]
        self.assertIsNotNone(game_out.board.dice)
        self.assertTrue(game_out.is_rolling)

        # Stop game and verify it halts cleanly
        self.game.stopped = True
        # Drain generator
        for _ in gen:
            pass
        self.assertFalse(self.game.is_running)


if __name__ == "__main__":
    unittest.main()
