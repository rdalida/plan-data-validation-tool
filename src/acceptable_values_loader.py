# src/validator/acceptable_values_loader.py
import json
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "User Configs"
VALUES_PATH = CONFIG_DIR / "acceptable_values.json"

def load_acceptable_values():
    try:
        with open(VALUES_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️ acceptable_values.json not found")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse acceptable_values.json: {e}")
        return {}
