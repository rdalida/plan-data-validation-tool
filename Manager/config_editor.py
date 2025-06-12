# Manager/config_editor.py

import json
from pathlib import Path
from .schema_model import ValidationSchema

# Shared user config path — same as SHM Validator
CONFIG_DIR = Path(__file__).resolve().parent.parent / "User Configs"

def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


class ConfigEditor:
    def __init__(self):
        self.schema: ValidationSchema | None = None
        self.filepath: Path | None = None

    def load_config(self, filepath: str):
        with open(filepath, 'r') as f:
            data = json.load(f)
        self.filepath = Path(filepath)
        self.schema = ValidationSchema.from_dict(data)

    def save_config(self):
        if not self.filepath or not self.schema:
            raise ValueError("No config file loaded.")
        with open(self.filepath, 'w') as f:
            json.dump(self.schema.to_dict(), f, indent=4)

    def get_default_config_dir(self) -> Path:
        ensure_config_dir()
        return CONFIG_DIR
