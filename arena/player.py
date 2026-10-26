import json
import random
import time

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
        self.last_failure_stage = None
        self.last_failure_reason = None

    def system(self, board) -> str:
        legal_moves = board.legal_moves()
        sample_token = legal_moves[0] if legal_moves else 0
        return f"""You are playing Ludo as {self.color}. Players: Red, Green, Yellow, Blue, each a different AI model, each with 4 tokens.
Rules: a token leaves base only on a roll of 6. Rolling a 6 grants an extra turn; three 6s in a row forfeits the turn. Landing on a lone opponent token on a non-safe square sends it back to base. Safe squares are the 4 start squares and 4 star squares. A token needs the exact roll to reach the finish. First to bring all 4 tokens home wins.
The dice has already been rolled for you: it shows {board.dice}.
You must pick one token id from these legal moves: {legal_moves}.
Each of threats, opportunities, and strategy MUST be ONE short sentence, no more than 12-15 words. Do not write multiple sentences or lists in any field.
Your ENTIRE response must be ONLY the JSON object. Do not include any text, explanation, or markdown code fences before or after it.
You should respond in JSON according to this spec:
{{
    "threats": "one short sentence or None",
    "opportunities": "one short sentence",
    "strategy": "one short sentence thought process",
    "token": {sample_token}
}}
The "token" field must be an integer from your legal moves list: {legal_moves}.
"""

    def user(self, board) -> str:
        legal_moves = board.legal_moves()
        board_json = board.json()
        board_alt = board.alternative()
        sample_token = legal_moves[0] if legal_moves else 0

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
    "token": {sample_token}
}}

Example 1:
{{
    "threats": "None.",
    "opportunities": "Advance Token 0.",
    "strategy": "Move Token 0 forward with dice roll.",
    "token": {sample_token}
}}

Example 2:
{{
    "threats": "Opponent token is nearby.",
    "opportunities": "Safe square within reach.",
    "strategy": "Advance active piece to safe zone.",
    "token": {sample_token}
}}

Remember: The JSON must have exactly the fields "threats", "opportunities", "strategy", and "token".
The "token" field must be an integer from your legal moves list: {legal_moves}.
Your ENTIRE response must be ONLY the JSON object. Do not include any text, explanation, or markdown code fences before or after it.
Now make your decision.
"""

    def _parse_response(self, text: str):
        if not text or not isinstance(text, str) or not text.strip():
            raise ValueError("empty_response: Model returned empty or whitespace text")

        clean_text = text.strip()

        # a) Strip markdown code fences (```json ... ``` or ``` ... ```)
        if "```" in clean_text:
            lines = clean_text.splitlines()
            filtered = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("```"):
                    continue
                filtered.append(line)
            fence_stripped = "\n".join(filtered).strip()
            if fence_stripped:
                clean_text = fence_stripped

        # Try parsing directly
        try:
            return json.loads(clean_text)
        except json.JSONDecodeError:
            pass

        # b) If string doesn't start with '{' or has preamble/trailing text,
        # extract substring between first '{' and last '}'
        start = clean_text.find("{")
        end = clean_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            json_substr = clean_text[start : end + 1]
            try:
                return json.loads(json_substr)
            except json.JSONDecodeError:
                pass

        # Also try on original text in case fence stripping altered something
        start_orig = text.find("{")
        end_orig = text.rfind("}")
        if start_orig != -1 and end_orig != -1 and end_orig > start_orig:
            json_substr_orig = text[start_orig : end_orig + 1]
            try:
                return json.loads(json_substr_orig)
            except json.JSONDecodeError as err:
                raise ValueError(f"raw_truncation: Unterminated or invalid JSON substring ({err})")

        if "{" not in text or "}" not in text:
            raise ValueError("non_json_preamble: No JSON object brackets found in response")

        raise ValueError(f"malformed_json: Could not parse JSON from response: {repr(clean_text[:100])}")

    def process_move(self, board) -> bool:
        legal_moves = board.legal_moves()
        if not legal_moves:
            return False

        self.used_fallback = False
        self.last_failure_stage = None
        self.last_failure_reason = None
        sys_prompt = self.system(board)
        usr_prompt = self.user(board)

        data = None
        raw_response = ""
        max_attempts = 3
        curr_usr_prompt = usr_prompt

        failure_stage = None
        failure_reason = None

        for attempt in range(1, max_attempts + 1):
            try:
                raw_response = self.llm.chat(sys_prompt, curr_usr_prompt, max_tokens=1000)
                data = self._parse_response(raw_response)

                if not isinstance(data, dict):
                    failure_stage = "bad_field_name"
                    failure_reason = f"Response parsed but is not a dict: {type(data)}"
                    raise ValueError(failure_reason)

                # Validate token choice
                raw_token = data.get("token")
                try:
                    cand_token = int(raw_token)
                except (ValueError, TypeError):
                    failure_stage = "illegal_token"
                    failure_reason = f"Token field {repr(raw_token)} cannot be converted to integer"
                    raise ValueError(failure_reason)

                if cand_token not in legal_moves:
                    failure_stage = "illegal_token"
                    failure_reason = f"Token {cand_token} is not in legal moves {legal_moves}"
                    raise ValueError(failure_reason)

                # Successfully parsed and validated!
                token_choice = cand_token
                self.threats = str(data.get("threats", ""))
                self.opportunities = str(data.get("opportunities", ""))
                self.strategy = str(data.get("strategy", ""))
                return board.move(token_choice)

            except Exception as e:
                err_msg = str(e)
                if failure_stage is None:
                    err_lower = err_msg.lower()
                    if any(term in err_lower for term in ["rate limit", "429", "too many requests", "quota", "resource_exhausted", "timeout", "timed out", "503", "502"]):
                        failure_stage = "api_level_error"
                        failure_reason = err_msg
                    elif "raw_truncation" in err_msg or "unterminated string" in err_lower or "expecting" in err_lower:
                        failure_stage = "raw_truncation"
                        failure_reason = err_msg
                    elif "non_json_preamble" in err_msg:
                        failure_stage = "non_json_preamble"
                        failure_reason = err_msg
                    elif "empty_response" in err_msg or not raw_response:
                        failure_stage = "empty_response"
                        failure_reason = err_msg
                    elif isinstance(e, (ConnectionError, TimeoutError)):
                        failure_stage = "api_level_error"
                        failure_reason = err_msg
                    else:
                        failure_stage = "malformed_json"
                        failure_reason = err_msg

                if attempt < max_attempts:
                    # Short backoff on API rate limit or transient errors
                    if failure_stage == "api_level_error":
                        time.sleep(1.0)

                    truncated_reply = raw_response[:200] if raw_response else "empty / no response"
                    if failure_stage == "illegal_token":
                        correction = (
                            f"Your previous reply was parsed, but the 'token' field was invalid ({failure_reason}). "
                            f"You must pick an integer token ID from this exact list: {legal_moves}. "
                            f"Reply again with ONLY a complete, valid JSON object."
                        )
                    else:
                        correction = (
                            f"Your previous reply could not be parsed as JSON. It was: {repr(truncated_reply)}. "
                            f"Error: {failure_reason}. "
                            f"Reply again with ONLY a complete, valid JSON object, no other text."
                        )

                    curr_usr_prompt = usr_prompt + "\n\n" + correction
                    failure_stage = None
                    failure_reason = None
                else:
                    if failure_stage is None:
                        failure_stage = "retries_exhausted"

        # If all 3 attempts failed, record and log failure stage
        self.used_fallback = True
        self.last_failure_stage = failure_stage or "retries_exhausted"
        self.last_failure_reason = failure_reason or "All attempts failed"

        print(
            f"[Player {self.color}] Fallback move triggered for {self.model} "
            f"(Failure stage: {self.last_failure_stage}). Reason: {self.last_failure_reason}"
        )
        if raw_response:
            print(f"[Player {self.color}] Last raw response was: {repr(raw_response[:200])}")

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
