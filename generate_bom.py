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
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        repo = url.replace("https://github.com", "").replace("git@github.com:", "").removesuffix(".git")
        return f"https://raw.githubusercontent.com{repo}/main", f"https://github.com{repo}/blob/main"
    except Exception:
        return ".", "."


def check(v):
    return f"**{v}**" if v and str(v).strip() else "A definir"


def to_github_anchor(heading_text):
    anchor = heading_text.lower()
    anchor = re.sub(r'[^\w\s-]', '', anchor)
    anchor = anchor.replace('_', '-')
    anchor = re.sub(r'\s+', '-', anchor.strip())
    anchor = re.sub(r'-+', '-', anchor)
    return anchor.strip('-')


def module_title(name):
    return "📦 " + name.replace('_', ' ').capitalize()


def generate_bom():
    root = Path(".")
    arc_dir = root / "archives"

    if arc_dir.exists():
        shutil.rmtree(arc_dir)
    arc_dir.mkdir()

    raw_url, blob_url = get_repo_info()

    existing_data = {}
    if Path(SETTINGS_FILE).exists():
        try:
            existing_data = json.loads(Path(SETTINGS_FILE).read_text(encoding="utf-8"))
        except Exception:
            pass

    existing_common = existing_data.get("COMMON_SETTINGS", {})
    new_data = {"COMMON_SETTINGS": {k: existing_common.get(k) for k in COMMON_KEYS}}

    sections = [
        (m, l1.name)
        for l1 in sorted(d for d in root.iterdir() if d.is_dir() and d.name not in EXCLUDE)
        for m in sorted(d for d in l1.iterdir() if d.is_dir())
        if any(m.rglob("*.stl"))
    ]

    module_headings = {
        m.name: module_title(m.name)
        for m, _ in sections
    }

    md = ["# Nomenclature (BOM)\n", "## Sommaire"]

    md += [
        "- [" + module_headings[m.name] + "](#" + to_github_anchor(module_headings[m.name]) + ")"
        for m, _ in sections
    ]

    c = new_data["COMMON_SETTINGS"]
    md += [
        "\n---\n", "## Parametres d'Impression\n",
        "| Parametre | Valeur |",
        "| :--- | :--- |",
        "| Couches | " + check(c.get('top_solid_layers')) + " / " + check(c.get('bottom_so
