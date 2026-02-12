import json
import shutil
import subprocess
import urllib.parse
from pathlib import Path
from contextlib import suppress

# --- CONFIGURATION ---
OUTPUT_FILE = "bom.md"
SETTINGS_FILE = "print_settings.json"
EXCLUDE = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives'}
COMMON_KEYS = [
    "top_solid_layers", "bottom_solid_layers", 
    "fill_density", "fill_pattern", 
    "infill_anchor", "infill_anchor_max"
]

def get_raw_url():
    """Récupère l'URL de base GitHub Raw pour les liens de téléchargement."""
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        # Nettoyage pour obtenir le chemin utilisateur/depot
        path = url.split("github.com")[-1].replace(".git", "").replace("git@github.com:", "/")
        if not path.startswith("/"): path = "/" + path
        return f"https://raw.githubusercontent.com{path}/main"
    except Exception:
        return "."

def generate_bom():
    root = Path(".")
    archive_dir = root / "archives"
    archive_dir.mkdir(exist_ok=True)
    
    settings_path = root / SETTINGS_FILE
    raw_url = get_raw_url()
    
    # 1. Chargement sécurisé des réglages
    existing_data = {}
    if settings_path.exists():
        with suppress(json.JSONDecodeError):
            existing_data = json.loads(settings_path.read_text(encoding="utf-8"))

    # Initialisation des paramètres communs
    new_data = {"COMMON_SETTINGS": {k: existing_data.get("COMMON_SETTINGS", {}).get(k) for k in COMMON_KEYS}}
    
    # 2. Analyse de l'arborescence (Modules de niveau 2)
    sections = []
    level1_dirs = sorted([d for d in root.iterdir() if d.is_dir() and d.name not in EXCLUDE])
    for l1 in level1_dirs:
        for m in sorted([d for d in l1.iterdir() if d.is_dir()]):
            if any(m.rglob("*.stl")):
                sections.append((m, l1.name))

    # 3. Préparation du contenu Markdown
    md = ["# 🛠️ Nomenclature (BOM)\n", "## 📌 Sommaire"]
    
    for mod_path, _ in sections:
        clean_name = mod_path.name.replace('_', ' ').capitalize()
        anchor = mod_path.name.lower().replace(" ", "-").replace("_", "-")
        md.append(f"- [{clean_name}](#-{anchor})")
    
    # Paramètres d'impression généraux
    c = new_data["COMMON_SETTINGS"]
    def check(v): return f"**{v}**" if v and str(v).strip() else "🔴 _
