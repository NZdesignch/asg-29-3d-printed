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
# Chargement / MAJ print settings (NON destructive)
# =====================
def load_or_create_print_settings(repo_root: Path):
    path = repo_root / PRINT_SETTINGS_FILE

    if not path.exists():
        data = {"global": {}, "parts": {}}
    else:
        data = json.loads(path.read_text(encoding="utf-8"))

    data.setdefault("global", {})
    data.setdefault("parts", {})

    return data, path


def sync_print_settings(stl_paths, settings):
    """Ajoute les STL manquants sans modifier l'existant"""
    parts = settings["parts"]
    updated = False

    for rel_path in stl_paths:
        if rel_path not in parts:
            parts[rel_path] = {"perimeters": None}
            updated = True
        else:
            parts[rel_path].setdefault("perimeters", parts[rel_path].get("perimeters"))

    return updated


def perimeters_status(rel_path: str, settings: dict) -> str:
    parts = settings["parts"]

    if rel_path not in parts:
        return "🔴"

    if parts[rel_path].get("perimeters") is not None:
        return "🟢"

    return "🟡"


# =====================
# Liens GitHub encodés
# =====================
def view_icon(path: str) -> str:
