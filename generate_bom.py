import json
import re
import shutil
import subprocess
import urllib.parse
from pathlib import Path

# --- CONFIGURATION ---
OUTPUT_FILE = "bom.md"
SETTINGS_FILE = "print_settings.json"

EXCLUDE = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives', 'previews'}

COMMON_KEYS = [
    "top_solid_layers", "bottom_solid_layers",
    "fill_density", "fill_pattern",
    "infill_anchor", "infill_anchor_max"
]


def get_repo_info():
    """
    Recupere les URLs de base du depot GitHub via git.
    Retourne (raw_url, blob_url) pour construire les liens vers les fichiers.
    En cas d'echec (pas de depot git), retourne (".", ".").
    """
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        repo = url.replace("https://github.com", "").replace("git@github.com:", "").removesuffix(".git")
        return f"https://raw.githubusercontent.com{repo}/main", f"https://github.com{repo}/blob/main"
    except:
        return ".", "."


def check(v):
    """
    Formate une valeur pour l'affichage Markdown.
    Si la valeur est definie et non vide : retourne la valeur en gras.
    Sinon : retourne un indicateur visuel.
    """
    return f"**{v}**
