from pathlib import Path
import json

# =====================
# Configuration
# =====================
STL_DIR = "stl"
PRINT_SETTINGS_FILE = "print_settings.json"


def main():
    repo_root = Path(__file__).resolve().parent
    stl_root = repo_root / STL_DIR
    settings_path = repo_root / PRINT_SETTINGS_FILE

    if not stl_root.exists():
        raise RuntimeError("Le dossier 'stl/' est introuvable à la racine du dépôt")

    # Charger ou initialiser print_settings.json
    if settings_path.exists():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    else:
        settings = {}

    # Initialiser les sections si absentes
    settings.setdefault("COMMON_SETTINGS", {})
    settings.setdefault("parts", {})

    parts = settings["parts"]

    # Scanner tous les fichiers STL
    for stl_file in stl_root.rglob("*.stl"):
        rel_path = stl_file.relative_to(repo_root).as_posix()

        # Ajouter la pièce si absente
        if rel_path not in parts:
            parts[rel_path] = {"perimeters": None}

    # Écriture SYSTÉMATIQUE (non destructive)
    settings_path.write_text(
