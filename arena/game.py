import pandas as pd
from arena.board import Board, RED, GREEN, YELLOW, BLUE, OFFSETS, SAFE_SQUARES, display_token
from arena.player import Player
from arena.record import record_game, get_games, get_ratings


class Game:
    def __init__(
        self,
        red_model: str = "gemini-2.5-flash",
        green_model: str = "gpt-oss-20b (Groq)",
        yellow_model: str = "gpt-oss-120b (Groq)",
        blue_model: str = "gpt-oss-120b (OpenRouter)"
    ):
        self.board = Board()
        self.players = {
            RED: Player(RED, red_model),
            GREEN: Player(GREEN, green_model),
            YELLOW: Player(YELLOW, yellow_model),
            BLUE: Player(BLUE, blue_model)
        }
        self._recorded = False
        self.stopped = False
        self.is_running = False
        self.is_rolling = False
        self.move_history = []

    @property
    def red_player(self):
        return self.players[RED]

    @property
    def green_player(self):
        return self.players[GREEN]

    @property
    def yellow_player(self):
        return self.players[YELLOW]

    @property
    def blue_player(self):
        return self.players[BLUE]

    def roll(self, forced_roll=None) -> int:
        if not self.board.is_active():
            return self.board.dice
        self.is_rolling = True
        return self.board.roll_dice(forced_roll=forced_roll)

    def resolve_move(self) -> Board:
        self.is_rolling = False
        if not self.board.is_active():
            return self.board

        curr_color = getattr(self.board, "dice_player", None) or self.board.current_player
        player = self.players[curr_color]

        legal_moves = self.board.legal_moves()
        if not legal_moves:
            player_str = f"{curr_color} ({player.model})"
            self.move_history.append({
                "Player": player_str,
                "Position": "-",
                "Result": "Skipped turn"
            })
        else:
            prev_tokens = list(self.board.tokens[curr_color])
            player.process_move(self.board)

            latest_token = self.board.latest_token
            if latest_token is not None:
                d_token = display_token(latest_token)
                prev_p = prev_tokens[latest_token]
                new_p = self.board.tokens[curr_color][latest_token]

                if new_p == -1:
                    pos_text = f"Token {d_token} -> base"
                elif new_p == 56:
                    pos_text = f"Token {d_token} -> finished"
                elif new_p >= 51:
                    pos_text = f"Token {d_token} -> home column"
                else:
                    abs_sq = (OFFSETS[curr_color] + new_p) % 52
                    pos_text = f"Token {d_token} -> square {abs_sq}"

                is_fallback = getattr(player, "used_fallback", False)
                abs_sq = (OFFSETS[curr_color] + new_p) % 52 if 0 <= new_p <= 50 else None
                is_safe = (abs_sq in SAFE_SQUARES) if abs_sq is not None else False
                is_capture = "Captured" in self.board.last_action_msg

                if new_p == 56:
                    res_text = "Finished"
                elif is_capture:
                    res_text = "Captured opponent's token"
                    for c in [RED, GREEN, YELLOW, BLUE]:
                        if f"Captured {c}" in self.board.last_action_msg:
                            res_text = f"Captured {c}'s token"
                            break
                elif new_p >= 51 and prev_p < 51:
                    res_text = "Reached home"
                elif is_safe:
                    res_text = "Reached safe square"
                elif prev_p == -1 and new_p == 0:
                    res_text = "Left base"
                elif is_fallback:
                    res_text = "Fallback move"
                else:
                    res_text = "Moved"

                player_str = f"{curr_color} ({player.model})"
                self.move_history.append({
                    "Player": player_str,
                    "Position": pos_text,
                    "Result": res_text
                })

        if not self.board.is_active() and not self._recorded:
            self.record()
            self._recorded = True

        return self.board

    def move(self) -> Board:
        self.roll()
        return self.resolve_move()

    def thoughts(self, color: str) -> str:
        if color in self.players:
            return self.players[color].thoughts()
        return ""

    def reset(self):
        self.stopped = True
        self.is_running = False
        self.is_rolling = False
        self.board = Board()
        self._recorded = False
        self.move_history = []
        for p in self.players.values():
            p.used_fallback = False
            p.threats = ""
            p.opportunities = ""
            p.strategy = ""

    def get_move_history(self) -> pd.DataFrame:
        cols = ["Player", "Position", "Result"]
        if not self.move_history:
            return pd.DataFrame(columns=cols)
        return pd.DataFrame(list(reversed(self.move_history)))[cols]

    def record(self):
        record_game(
            red_model=self.red_player.model,
            green_model=self.green_player.model,
            yellow_model=self.yellow_player.model,
            blue_model=self.blue_player.model,
            winner=self.board.winner,
            finish_ranks=self.board.finish_ranks,
            turns=self.board.turns_played
        )

    @classmethod
    def get_games(cls):
        return get_games()

    @classmethod
    def get_ratings(cls):
        return get_ratings()
