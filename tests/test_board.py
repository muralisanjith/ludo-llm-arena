import unittest
from arena.board import Board, RED, GREEN, YELLOW, BLUE, SAFE_SQUARES, OFFSETS, display_token


class TestLudoBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board()

    def test_base_exit_on_6(self):
        # Initial state: all tokens in base (-1)
        self.assertEqual(self.board.tokens[RED], [-1, -1, -1, -1])

        # Roll 5: no legal moves, turn auto-skips to Green
        roll = self.board.roll_dice(forced_roll=5)
        self.assertEqual(roll, 5)
        self.assertEqual(self.board.legal_moves(), [])
        self.assertEqual(self.board.current_player, GREEN)

        # Reset to RED for testing 6
        self.board.current_player_idx = 0
        roll = self.board.roll_dice(forced_roll=6)
        self.assertEqual(roll, 6)
        self.assertEqual(self.board.legal_moves(), [0, 1, 2, 3])

        # Move token 0 out of base
        success = self.board.move(0)
        self.assertTrue(success)
        self.assertEqual(self.board.tokens[RED][0], 0)  # Progress 0 (Start square)

    def test_home_entry_and_exact_finish(self):
        # Set token 0 of RED at progress 50 (last square of track)
        self.board.tokens[RED][0] = 50

        # Roll 3: should move to home stretch step 3 (progress 53)
        self.board.roll_dice(forced_roll=3)
        self.assertEqual(self.board.legal_moves(), [0])
        self.board.move(0)
        self.assertEqual(self.board.tokens[RED][0], 53)

        # Now token 0 is at progress 53. Finish is 56 (needs roll of 3)
        # Roll 5: overshooting (53 + 5 = 58 > 56), so invalid move
        self.board.current_player_idx = 0
        self.board.roll_dice(forced_roll=5)
        self.assertNotIn(0, self.board.legal_moves())

        # Roll 3: exact finish
        self.board.current_player_idx = 0
        self.board.roll_dice(forced_roll=3)
        self.assertIn(0, self.board.legal_moves())
        self.board.move(0)
        self.assertEqual(self.board.tokens[RED][0], 56)

    def test_capture(self):
        # RED token 0 at progress 10 -> absolute square (0 + 10) % 52 = 10 (non-safe square)
        self.board.tokens[RED][0] = 10
        # GREEN token 0 at progress 0 -> absolute square (13 + 0) % 52 = 13
        # If GREEN moves token 0 by rolling... wait!
        # Set GREEN token 0 at progress 48 -> absolute square (13 + 48) % 52 = 61 % 52 = 9
        self.board.tokens[GREEN][0] = 48

        # GREEN's turn
        self.board.current_player_idx = 1  # GREEN
        self.board.roll_dice(forced_roll=1)  # 48 + 1 = 49 -> abs square (13 + 49) % 52 = 62 % 52 = 10
        self.board.move(0)

        # GREEN landed on 10, capturing RED token 0!
        self.assertEqual(self.board.tokens[RED][0], -1)  # Sent back to base
        self.assertEqual(self.board.tokens[GREEN][0], 49)
        # Capturing grants extra turn, so current player is still GREEN
        self.assertEqual(self.board.current_player, GREEN)

    def test_safe_squares_no_capture(self):
        # Star square 8 is safe.
        # RED token 0 at progress 8 -> absolute square 8
        self.board.tokens[RED][0] = 8
        # GREEN token 0 at progress 47 -> absolute square (13 + 47) % 52 = 60 % 52 = 8
        self.board.tokens[GREEN][0] = 46

        # GREEN's turn, roll 1 -> progress 47, abs square 8
        self.board.current_player_idx = 1  # GREEN
        self.board.roll_dice(forced_roll=1)
        self.board.move(0)

        # Both tokens present on safe square 8, NO capture
        self.assertEqual(self.board.tokens[RED][0], 8)
        self.assertEqual(self.board.tokens[GREEN][0], 47)

    def test_three_consecutive_sixes(self):
        # Roll 6 three times in a row
        self.board.roll_dice(forced_roll=6)
        self.board.move(0)  # Move out of base
        self.assertEqual(self.board.current_player, RED)  # Extra turn

        self.board.roll_dice(forced_roll=6)
        self.board.move(0)  # Move forward
        self.assertEqual(self.board.current_player, RED)  # Extra turn

        # 3rd roll of 6 -> turn forfeited, passes to GREEN
        self.board.roll_dice(forced_roll=6)
        self.assertEqual(self.board.current_player, GREEN)

    def test_continuous_dice_rolls_20_plus_turns(self):
        import random
        random.seed(42)
        rolls = []
        for _ in range(25):
            roll = self.board.roll_dice()
            self.assertIn(roll, range(1, 7))
            self.assertEqual(self.board.dice, roll)
            rolls.append(roll)
            lm = self.board.legal_moves()
            if lm:
                self.board.move(lm[0])

        self.assertEqual(len(rolls), 25)
        self.assertGreater(len(set(rolls)), 1)

    def test_display_token(self):
        self.assertEqual(display_token(0), 1)
        self.assertEqual(display_token(1), 2)
        self.assertEqual(display_token(2), 3)
        self.assertEqual(display_token(3), 4)
        self.assertEqual(display_token("0"), 1)

        # Ensure board.last_action_msg uses 1-indexed token display
        self.board.roll_dice(forced_roll=6)
        self.board.move(0)
        self.assertIn("moved token 1", self.board.last_action_msg)


if __name__ == "__main__":
    unittest.main()
