import random
import json

RED = "Red"
GREEN = "Green"
YELLOW = "Yellow"
BLUE = "Blue"

PLAYERS = [RED, GREEN, YELLOW, BLUE]

OFFSETS = {
    RED: 0,
    GREEN: 13,
    YELLOW: 26,
    BLUE: 39
}

# 4 start squares (0, 13, 26, 39) + 4 star squares (8, 21, 34, 47)
SAFE_SQUARES = {0, 8, 13, 21, 26, 34, 39, 47}

pieces = {
    RED: "Red (🔴)",
    GREEN: "Green (🟢)",
    YELLOW: "Yellow (🟡)",
    BLUE: "Blue (🔵)"
}

def display_token(token_id) -> int:
    """Return 1-indexed token number (1-4) for user-facing display."""
    try:
        return int(token_id) + 1
    except (ValueError, TypeError):
        return token_id


class Board:
    """
    Ludo engine supporting 4 players (Red, Green, Yellow, Blue).
    Tokens progress:
      -1  : Base (yard)
      0..50: Shared 52-square outer track (0 = player's start square)
      51..55: Home column (5 steps)
      56  : Finished
    """
    def __init__(self):
        self.tokens = {
            RED: [-1, -1, -1, -1],
            GREEN: [-1, -1, -1, -1],
            YELLOW: [-1, -1, -1, -1],
            BLUE: [-1, -1, -1, -1]
        }
        self.current_player_idx = 0
        self.dice = None
        self.dice_player = None
        self.consecutive_sixes = 0
        self.turns_played = 0
        self.forfeit = False
        self.winner = None
        self.latest_color = None
        self.latest_token = None
        self.last_action_msg = ""
        self.finish_ranks = []
        self.roll_count = 0

    @property
    def current_player(self):
        return PLAYERS[self.current_player_idx]

    def height(self):
        return 15

    def is_player_finished(self, color):
        return all(p == 56 for p in self.tokens[color])

    def _all_finished(self):
        return len(self.finish_ranks) >= 3 or all(self.is_player_finished(c) for c in PLAYERS)

    def _next_turn(self):
        self.turns_played += 1
        if self._all_finished() or self.turns_played >= 300:
            return

        # Advance to next unfinished player
        for _ in range(4):
            self.current_player_idx = (self.current_player_idx + 1) % 4
            if not self.is_player_finished(self.current_player):
                break

    def roll_dice(self, forced_roll=None):
        if not self.is_active():
            return self.dice

        self.dice_player = self.current_player
        self.dice = forced_roll if forced_roll is not None else random.randint(1, 6)
        self.roll_count += 1

        if self.dice == 6:
            self.consecutive_sixes += 1
            if self.consecutive_sixes == 3:
                self.last_action_msg = f"{self.current_player} rolled three 6s in a row! Turn forfeited."
                self.consecutive_sixes = 0
                self._next_turn()
                return self.dice
        else:
            self.consecutive_sixes = 0

        lm = self.legal_moves()
        if len(lm) == 0:
            self.last_action_msg = f"{self.current_player} rolled {self.dice} but has no legal moves."
            if self.dice != 6:
                self.consecutive_sixes = 0
                self._next_turn()

        return self.dice

    def legal_moves(self):
        if self.dice is None or not self.is_active():
            return []

        moves = []
        for t_id, prog in enumerate(self.tokens[self.current_player]):
            if prog == -1:
                if self.dice == 6:
                    moves.append(t_id)
            elif prog < 56:
                new_p = prog + self.dice
                if new_p <= 56:
                    moves.append(t_id)
        return moves

    def illegal_moves(self):
        all_moves = [0, 1, 2, 3]
        lm = set(self.legal_moves())
        return [m for m in all_moves if m not in lm]

    def move(self, token_id):
        if not self.is_active():
            return False

        try:
            token_id = int(token_id)
        except (ValueError, TypeError):
            return False

        if token_id not in self.legal_moves():
            return False

        prog = self.tokens[self.current_player][token_id]
        if prog == -1:
            new_p = 0
        else:
            new_p = prog + self.dice

        self.tokens[self.current_player][token_id] = new_p
        self.latest_color = self.current_player
        self.latest_token = token_id

        captured = False
        captured_color = None
        # Check capture if on outer track
        if 0 <= new_p <= 50:
            abs_sq = (OFFSETS[self.current_player] + new_p) % 52
            if abs_sq not in SAFE_SQUARES:
                for opp_color in PLAYERS:
                    if opp_color == self.current_player:
                        continue
                    for opp_t_id, opp_p in enumerate(self.tokens[opp_color]):
                        if 0 <= opp_p <= 50:
                            opp_abs_sq = (OFFSETS[opp_color] + opp_p) % 52
                            if opp_abs_sq == abs_sq:
                                self.tokens[opp_color][opp_t_id] = -1
                                captured = True
                                captured_color = opp_color

        # Check winner / finish ranks
        if self.is_player_finished(self.current_player):
            if self.current_player not in self.finish_ranks:
                self.finish_ranks.append(self.current_player)
            if self.winner is None:
                self.winner = self.current_player

        msg_parts = [f"{self.current_player} moved token {display_token(token_id)} (rolled {self.dice})."]
        if captured:
            msg_parts.append(f"Captured {captured_color}'s token!")
        if new_p == 56:
            msg_parts.append(f"Token {display_token(token_id)} reached home!")
        self.last_action_msg = " ".join(msg_parts)

        # Extra turn conditions: roll 6, capture, or token finished
        extra_turn = (self.dice == 6 or captured or new_p == 56) and self.is_active()

        if not extra_turn:
            self.consecutive_sixes = 0
            self._next_turn()

        return True

    def is_active(self):
        if self.forfeit:
            return False
        if self.winner is not None:
            return False
        if self.turns_played >= 300:
            return False
        return True

    def message(self):
        if self.forfeit:
            return f"Game forfeited by {self.current_player}."
        if self.winner:
            return f"{self.winner} wins!"
        if self.turns_played >= 300:
            return "Game over: maximum turns (300) reached."
        if self.last_action_msg:
            base = self.last_action_msg + " "
        else:
            base = ""
        if self.dice is not None:
            return f"{base}{self.current_player}'s turn. Rolled {self.dice}. Legal moves: {self.legal_moves()}"
        return f"{base}{self.current_player}'s turn."

    def json(self):
        return json.dumps({
            "current_player": self.current_player,
            "dice": self.dice,
            "legal_moves": self.legal_moves(),
            "tokens": self.tokens,
            "turns_played": self.turns_played,
            "winner": self.winner,
            "forfeit": self.forfeit,
            "finish_ranks": self.finish_ranks
        }, indent=2)

    def alternative(self):
        lines = [f"Current turn: {self.current_player} | Dice rolled: {self.dice}"]
        lines.append(f"Legal token IDs to move: {self.legal_moves()}")
        for color in PLAYERS:
            t_str = []
            for i, prog in enumerate(self.tokens[color]):
                if prog == -1:
                    pos = "Base"
                elif prog == 56:
                    pos = "Finished"
                elif prog >= 51:
                    pos = f"Home stretch (step {prog - 50}/5)"
                else:
                    abs_sq = (OFFSETS[color] + prog) % 52
                    is_safe = " [SAFE]" if abs_sq in SAFE_SQUARES else ""
                    pos = f"Track square {abs_sq}{is_safe} (progress {prog}/50)"
                t_str.append(f"Token {i}: {pos}")
            lines.append(f"{color}: " + " | ".join(t_str))
        return "\n".join(lines)
