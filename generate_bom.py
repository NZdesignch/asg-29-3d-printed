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
PRINT_SETTINGS_FILE = "print_settings.json"
STL_EXT = ".stl"


# =====================
# Print settings (NON destructif)
# =====================
def load_or_create_print_settings(repo_root: Path):
    path = repo_root / PRINT_SETTINGS_FILE
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {}

    data.setdefault("COMMON_SETTINGS", {})
    data.setdefault("parts", {})

    return data, path


def sync_print_settings(stl_paths, settings):
    """
    Ajoute les STL manquants sans jamais modifier
    une valeur déjà existante.
    """
    updated = False
    parts = settings["parts"]

    for rel_path in stl_paths:
        if rel_path not in parts:
            parts[rel_path] = {"perimeters": None}
            updated = True
        elif "perimeters" not in parts[rel_path]:
            parts[rel_path]["perimeters"] = None
            updated = True

    return updated


# =====================
# Lecture perimeters + statut
# =====================
def perimeters_value(rel_path, settings) -> str:
    part = settings.get("parts", {}).get(rel_path)
    if part and part.get("perimeters") is not None:
        return str(part["perimeters"])
    return ""


def status_icon(rel_path, settings) -> str:
    part = settings.get("parts", {}).get(rel_path)
    if part is None:
        return "🔴"
    if part.get("perimeters") is not None:
        return "🟢"
