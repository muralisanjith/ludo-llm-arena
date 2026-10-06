import os
import json
from datetime import datetime
import pandas as pd

RECORDS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "records.json")


def _load_records():
    if not os.path.exists(RECORDS_FILE):
        return []
    try:
        with open(RECORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_records(records):
    os.makedirs(os.path.dirname(RECORDS_FILE), exist_ok=True)
    with open(RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)


def record_game(red_model, green_model, yellow_model, blue_model, winner, finish_ranks=None, turns=0):
    records = _load_records()
    rec = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "red": red_model,
        "green": green_model,
        "yellow": yellow_model,
        "blue": blue_model,
        "winner": winner if winner else "Draw/Timeout",
        "finish_ranks": finish_ranks if finish_ranks else [],
        "turns": turns
    }
    records.append(rec)
    _save_records(records)


def get_games():
    records = _load_records()
    if not records:
        return pd.DataFrame(columns=["Date", "Red", "Green", "Yellow", "Blue", "Winner", "Turns"])
    rows = []
    for r in reversed(records):
        rows.append({
            "Date": r.get("date", ""),
            "Red": r.get("red", ""),
            "Green": r.get("green", ""),
            "Yellow": r.get("yellow", ""),
            "Blue": r.get("blue", ""),
            "Winner": r.get("winner", ""),
            "Turns": r.get("turns", 0)
        })
    return pd.DataFrame(rows)


def get_ratings():
    records = _load_records()
    stats = {}

    for r in records:
        models = {
            "Red": r.get("red"),
            "Green": r.get("green"),
            "Yellow": r.get("yellow"),
            "Blue": r.get("blue")
        }
        winner = r.get("winner")

        for color, model in models.items():
            if not model:
                continue
            if model not in stats:
                stats[model] = {"played": 0, "wins": 0}
            stats[model]["played"] += 1
            if winner == color or winner == model:
                stats[model]["wins"] += 1

    if not stats:
        return pd.DataFrame(columns=["Model", "Played", "Wins", "Win Rate"])

    rows = []
    for model, s in stats.items():
        played = s["played"]
        wins = s["wins"]
        win_rate = f"{(wins / played * 100):.1f}%" if played > 0 else "0.0%"
        rows.append({
            "Model": model,
            "Played": played,
            "Wins": wins,
            "Win Rate": win_rate
        })

    df = pd.DataFrame(rows)
    return df.sort_values(by=["Wins", "Played"], ascending=[False, True]).reset_index(drop=True)
