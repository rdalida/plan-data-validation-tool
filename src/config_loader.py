import os
import sys
import json
from pathlib import Path
from utils import get_config_dir

CONFIG_DIR = get_config_dir()



def ensure_config_dir():
    if not CONFIG_DIR.exists():
        print(f"⚠️ Config directory not found at: {CONFIG_DIR}")
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        print("🆕 Created empty User Configs folder.")

def load_all_configs():
    ensure_config_dir()
    configs = {}

    for file in CONFIG_DIR.glob("*.json"):
        role_name = file.stem.lower()
        try:
            with open(file, "r") as f:
                config = json.load(f)
                configs[role_name] = config
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse {file.name}: {e}")
        except Exception as e:
            print(f"❌ Error loading {file.name}: {e}")

    return configs
