import unittest
from arena.board import Board, RED
from arena.player import Player
from arena.llm import LLM


class MockLLM(LLM):
    def __init__(self, response_text: str):
        super().__init__("mock-model")
        self.response_text = response_text

    def chat(self, system: str, user: str, max_tokens: int = 150) -> str:
        return self.response_text


class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.board.roll_dice(forced_roll=6)  # Legal moves: [0, 1, 2, 3]

    def test_player_init(self):
        player = Player(RED, "gemini-2.5-flash")
        self.assertEqual(player.color, RED)
        self.assertEqual(player.model, "gemini-2.5-flash")
        self.assertEqual(player.evaluation, "")

    def test_thoughts_format(self):
        player = Player(RED, "gemini-2.5-flash")
        player.threats = "None"
        player.opportunities = "Advance token 0"
        player.strategy = "Move token 0"

        html = player.thoughts()
        self.assertNotIn("<b>Evaluation:</b>", html)
        self.assertIn("<b>Threats:</b> None", html)
        self.assertIn("<b>Opportunities:</b> Advance token 0", html)
        self.assertIn("<b>Strategy:</b> Move token 0", html)

    def test_valid_process_move(self):
        player = Player(RED, "gemini-2.5-flash")
        valid_json = """{
            "threats": "None",
            "opportunities": "Move piece out of base",
            "strategy": "Pick token 0",
            "token": "0"
        }"""
        player.llm = MockLLM(valid_json)

        success = player.process_move(self.board)
        self.assertTrue(success)
        self.assertEqual(player.strategy, "Pick token 0")
        self.assertEqual(self.board.tokens[RED][0], 0)
        self.assertFalse(player.used_fallback)

    def test_invalid_json_fallback(self):
        player = Player(RED, "gemini-2.5-flash")
        invalid_json = "I refuse to return JSON"
        player.llm = MockLLM(invalid_json)

        success = player.process_move(self.board)
        self.assertTrue(success)
        self.assertTrue(player.used_fallback)
        self.assertEqual(player.last_failure_stage, "non_json_preamble")
        self.assertNotIn("fallback", player.strategy.lower())
        self.assertEqual(player.strategy, "Played the best available move.")

    def test_markdown_fences_recovered(self):
        player = Player(RED, "gemini-2.5-flash")
        fenced_json = """```json
{
    "threats": "None",
    "opportunities": "Move out of base",
    "strategy": "Select token 0",
    "token": 0
}
```"""
        player.llm = MockLLM(fenced_json)
        success = player.process_move(self.board)
        self.assertTrue(success)
        self.assertFalse(player.used_fallback)
        self.assertEqual(player.strategy, "Select token 0")

    def test_preamble_and_trailing_text_recovered(self):
        player = Player(RED, "gemini-2.5-flash")
        noisy_json = """Sure, here is my decision:
{
    "threats": "Blue token nearby",
    "opportunities": "Safe square",
    "strategy": "Select token 0",
    "token": 0
}
Hope this helps!"""
        player.llm = MockLLM(noisy_json)
        success = player.process_move(self.board)
        self.assertTrue(success)
        self.assertFalse(player.used_fallback)
        self.assertEqual(player.strategy, "Select token 0")

    def test_retry_correction_success(self):
        # First attempt returns invalid, second attempt returns valid
        class MultiAttemptMockLLM(LLM):
            def __init__(self):
                super().__init__("mock-model")
                self.calls = 0

            def chat(self, system: str, user: str, max_tokens: int = 1000) -> str:
                self.calls += 1
                if self.calls == 1:
                    return "Here is some invalid text"
                return '{"threats": "None", "opportunities": "None", "strategy": "Move 0", "token": 0}'

        player = Player(RED, "gemini-2.5-flash")
        mock_llm = MultiAttemptMockLLM()
        player.llm = mock_llm

        success = player.process_move(self.board)
        self.assertTrue(success)
        self.assertFalse(player.used_fallback)
        self.assertEqual(mock_llm.calls, 2)


if __name__ == "__main__":
    unittest.main()
