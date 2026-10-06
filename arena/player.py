import json
import random

from arena.llm import LLM


class Player:
    def __init__(self, color: str, model: str):
        self.color = color
        self.colour = color  # support both spellings
        self.model = model
        self.llm = LLM.create(model)

        self.evaluation = ""
        self.threats = ""
        self.opportunities = ""
        self.strategy = ""
        self.used_fallback = False

    def system(self, board) -> str:
        legal_moves = board.legal_moves()
        return f"""You are playing Ludo as {self.color}. Players: Red, Green, Yellow, Blue, each a different AI model, each with 4 tokens.
Rules: a token leaves base only on a roll of 6. Rolling a 6 grants an extra turn; three 6s in a row forfeits the turn. Landing on a lone opponent token on a non-safe square sends it back to base. Safe squares are the 4 start squares and 4 star squares. A token needs the exact roll to reach the finish. First to bring all 4 tokens home wins.
The dice has already been rolled for you: it shows {board.dice}.
You must pick one token id from these legal moves: {legal_moves}.
Each of threats, opportunities, and strategy MUST be ONE short sentence, no more than 12-15 words. Do not write multiple sentences or lists in any field.
You should respond in JSON according to this spec:
{{
    "threats": "one short sentence or None",
    "opportunities": "one short sentence",
    "strategy": "one short sentence thought process",
    "token": "one id from this list of legal moves: {legal_moves}"
}}
You must pick one of these ids for your token: {legal_moves}
"""

    def user(self, board) -> str:
        legal_moves = board.legal_moves()
        board_json = board.json()
        board_alt = board.alternative()

        return f"""You are {self.color}. Your dice roll is {board.dice}.
Legal moves (token IDs you can choose from): {legal_moves}

Current Board State (JSON):
{board_json}

Current Board State (Text Summary):
{board_alt}

Respond ONLY with a JSON object matching this exact spec:
{{
    "threats": "one short sentence or None",
    "opportunities": "one short sentence",
    "strategy": "one short sentence thought process",
    "token": "one id from this list of legal moves: {legal_moves}"
}}

Example 1:
{{
    "threats": "None.",
    "opportunities": "Advance Token 0.",
    "strategy": "Move Token 0 forward with dice roll.",
    "token": "{legal_moves[0] if legal_moves else 0}"
}}

Example 2:
{{
    "threats": "Yellow token is 4 squares behind.",
    "opportunities": "Capture opportunity on track.",
    "strategy": "Select Token 1 to execute capture.",
    "token": "{legal_moves[0] if legal_moves else 0}"
}}

Now make your decision.
"""

    def _parse_response(self, text: str):
        # Extract JSON if enclosed in markdown code blocks
        clean_text = text.strip()
        if "```json" in clean_text:
            clean_text = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_text = clean_text.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            # Fallback: extract substring between first '{' and last '}'
            start = clean_text.find("{")
            end = clean_text.rfind("}")
            if start != -1 and end != -1 and end > start:
                json_str = clean_text[start : end + 1]
                return json.loads(json_str)
            raise

    def process_move(self, board) -> bool:
        legal_moves = board.legal_moves()
        if not legal_moves:
            return False

        self.used_fallback = False
        sys_prompt = self.system(board)
        usr_prompt = self.user(board)

        # Attempt 1
        data = None
        raw_response = ""
        try:
            raw_response = self.llm.chat(sys_prompt, usr_prompt, max_tokens=600)
            data = self._parse_response(raw_response)
        except Exception as e:
            # Attempt 2: Retry with error feedback
            retry_usr = usr_prompt + f"\n\nPrevious attempt failed with error: {str(e)}. Please return valid JSON matching the spec."
            try:
                raw_response = self.llm.chat(sys_prompt, retry_usr, max_tokens=600)
                data = self._parse_response(raw_response)
            except Exception as e2:
                print(f"[Player {self.color}] Error processing move for {self.model}: {e2}")
                if raw_response:
                    print(f"[Player {self.color}] Raw response was: {repr(raw_response)}")

        # Validate parsed data and token choice
        token_choice = None
        if data and isinstance(data, dict):
            self.threats = str(data.get("threats", ""))
            self.opportunities = str(data.get("opportunities", ""))
            self.strategy = str(data.get("strategy", ""))

            raw_token = data.get("token")
            try:
                cand_token = int(raw_token)
                if cand_token in legal_moves:
                    token_choice = cand_token
            except (ValueError, TypeError):
                pass

        # Fallback if invalid JSON or illegal token choice
        if token_choice is None:
            self.used_fallback = True
            token_choice = random.choice(legal_moves)
            if not self.threats:
                self.threats = "None."
            if not self.opportunities:
                self.opportunities = "Advance active token."
            self.strategy = "Played the best available move."

        return board.move(token_choice)

    def move(self, board) -> bool:
        return self.process_move(board)

    def _trunc(self, text: str, max_words: int = 20) -> str:
        words = text.split()
        if len(words) > max_words:
            return " ".join(words[:max_words]) + "..."
        return text

    def thoughts(self) -> str:
        threats_txt = self._trunc(self.threats) if self.threats else "-"
        opps_txt = self._trunc(self.opportunities) if self.opportunities else "-"
        strat_txt = self._trunc(self.strategy) if self.strategy else "-"

        return f"""<div class="thoughts-content">
<div><b>Threats:</b> {threats_txt}</div>
<div><b>Opportunities:</b> {opps_txt}</div>
<div><b>Strategy:</b> {strat_txt}</div>
</div>"""

    def switch_model(self, new_model: str):
        self.model = new_model
        self.llm = LLM.create(new_model)
