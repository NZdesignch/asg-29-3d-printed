from pathlib import Path
from urllib.parse import quote
import json

# =====================
# Configuration GitHub
# =====================
GITHUB_USER = "NZdesignch"
GITHUB_REPO = "asg-29-3d-printed"
GITHUB_BRANCH = "main"

# =====================
# Configuration projet
# =====================
STL_DIR = "stl"
OUTPUT_MD = "bom.md"
STL_EXT = ".stl"
PRINT_SETTINGS_FILE = "print_settings.json"


# =====================
# Chargement / création print_settings.json (NON destructif)
# =====================
def load_or_create_print_settings(repo_root: Path):
    path = repo_root / PRINT_SETTINGS_FILE

    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {}

    data.setdefault("global", {})
    data.setdefault("parts", {})

    return data, path


def sync_print_settings(found_stl_paths, settings):
    updated = False
    parts = settings["parts"]

    for rel_path in found_stl_paths:
        if rel_path not in parts:
            parts[rel_path] = {"perimeters": None}
            updated = True
        else:
