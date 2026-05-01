import json
import os

SAVE_PATH = "souls_save.json"


def load_high_score():
    try:
        with open(SAVE_PATH, "r") as f:
            data = json.load(f)
            return data.get("high_score", 0)
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def save_high_score(score):
    current = load_high_score()
    if score > current:
        with open(SAVE_PATH, "w") as f:
            json.dump({"high_score": score}, f)
        return True
    return False
