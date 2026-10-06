import sys
import os
import unittest

sys.path.insert(0, os.path.abspath("."))
from arena.board import Board, RED, GREEN, YELLOW, BLUE
from arena.board_view import to_svg


class TestBoardView(unittest.TestCase):
    def setUp(self):
        self.board = Board()

    def test_to_svg_basic(self):
        svg = to_svg(self.board)
        self.assertIn("<svg", svg)
        self.assertIn("</svg>", svg)
        self.assertIn("@keyframes dropPiece", svg)
        self.assertIn("<circle", svg)

    def test_to_svg_with_latest_move(self):
        self.board.roll_dice(forced_roll=6)
        self.board.move(0)  # Move Red token 0

        svg = to_svg(self.board)
        self.assertIn("new-piece", svg)
        self.assertIn("#EF4444", svg)

    def test_single_circle_token_states(self):
        from arena.board_view import BASE_TOKEN_TEXT_COLOR, TOKEN_TEXT_COLOR, LIGHT_HEX, COLOR_HEX
        # 1. State A: All 16 tokens in base initially (-1)
        # Should have light/pastel circles with centered number text in BASE_TOKEN_TEXT_COLOR
        svg = to_svg(self.board)
        # Numbers 1, 2, 3, 4 should all be present in base
        self.assertIn('>1</text>', svg)
        self.assertIn('>2</text>', svg)
        self.assertIn('>3</text>', svg)
        self.assertIn('>4</text>', svg)
        # Base text color should be present for all 4 players
        self.assertIn(f'fill="{BASE_TOKEN_TEXT_COLOR[RED]}"', svg)
        self.assertIn(f'fill="{BASE_TOKEN_TEXT_COLOR[GREEN]}"', svg)
        self.assertIn(f'fill="{BASE_TOKEN_TEXT_COLOR[YELLOW]}"', svg)
        self.assertIn(f'fill="{BASE_TOKEN_TEXT_COLOR[BLUE]}"', svg)

        # 2. State B: Move Red token 0 out of base (progress 0)
        self.board.roll_dice(forced_roll=6)
        self.board.move(0)
        svg_moved = to_svg(self.board)
        # Token 0 still displays as 1, but now with solid color fill and white text
        self.assertIn('>1</text>', svg_moved)
        self.assertIn(f'fill="{TOKEN_TEXT_COLOR[RED]}"', svg_moved)
        self.assertIn(f'fill="{COLOR_HEX[RED]}" stroke="#FFFFFF"', svg_moved)

        # 3. Capture Reversion: Set Red token 0 back to base (-1)
        # Red token 0 back in base (-1) -> reverts to pastel look with number still showing
        self.board.tokens[RED][0] = -1
        svg_captured = to_svg(self.board)
        self.assertIn('>1</text>', svg_captured)
        self.assertIn(f'fill="{LIGHT_HEX[RED]}" stroke="{COLOR_HEX[RED]}"', svg_captured)
        self.assertIn(f'fill="{BASE_TOKEN_TEXT_COLOR[RED]}"', svg_captured)

    def test_token_text_contrast_and_single_circle(self):
        from arena.board import GREEN, YELLOW, BLUE
        # Put 1 token from each player on track
        self.board.tokens[RED][0] = 0
        self.board.tokens[GREEN][0] = 0
        self.board.tokens[YELLOW][0] = 0
        self.board.tokens[BLUE][0] = 0

        svg = to_svg(self.board)

        # Confirm Yellow uses dark text for contrast
        self.assertIn('fill="#1F2937"', svg)
        # Confirm Red/Green/Blue use white text
        self.assertIn('fill="#FFFFFF"', svg)

        # Count token circles: exactly 16 tokens on board
        # Class token is applied to all token circles
        token_circles = [part for part in svg.split('<circle') if 'class="token' in part]
        self.assertEqual(len(token_circles), 16)


if __name__ == "__main__":
    unittest.main()
