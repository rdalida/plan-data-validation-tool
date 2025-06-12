import subprocess
import re

print("🚀 Running version update script")

VERSION_FILE = "src/version.py"
VARIABLE_NAME = "APP_VERSION"

# Get latest Git tag (e.g. v0.1.3) and strip "v"
tag = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], text=True).strip()
version = tag.lstrip("v")

# Read and update the version string
with open(VERSION_FILE, "r") as f:
    content = f.read()

pattern = rf'({VARIABLE_NAME}\s*=\s*["\'])[^"\']+(["\'])'
updated = re.sub(pattern, lambda m: f'{m.group(1)}{version}{m.group(2)}', content)

with open(VERSION_FILE, "w") as f:
    f.write(updated)

print(f"✅ Updated {VERSION_FILE} to version {version}")
