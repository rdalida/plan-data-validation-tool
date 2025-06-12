import os
import sys
from pathlib import Path

def get_resource_path(relative_path):
    """Get absolute path to bundled resource (e.g. icon), works in dev and PyInstaller."""
    try:
        base_path = sys._MEIPASS  # PyInstaller unpack dir
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_config_dir():
    """
    Get absolute path to shared 'User Configs' folder.
    - In frozen mode: ../User Configs (sibling to app folder)
    - In dev mode: walk up to find a 'User Configs' folder
    """
    if getattr(sys, 'frozen', False):
        # In PyInstaller exe: go up from /dist/SHMValidator or /ConfigManager
        return Path(sys.executable).parent.parent / "User Configs"
    else:
        # In dev: try to locate by walking upward
        here = Path(__file__).resolve()
        for parent in here.parents:
            if (parent / "User Configs").exists():
                return parent / "User Configs"
        # fallback if nothing found (creates in project root)
        return Path.cwd().parent / "User Configs"
