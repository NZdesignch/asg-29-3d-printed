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
    Ajoute les STL manquants dans print_settings.json
    sans jamais écraser une valeur existante.
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
    return "🟡"


# =====================
# Liens GitHub (icônes cliquables)
# =====================
def view_icon(path: str) -> str:
    url = (
        f"https://github.com/{GITHUB_USER}/"
        f"{GITHUB_REPO}/blob/{GITHUB_BRANCH}/"
        f"{quote(path)}"
    )
    return f"[🔍]({url})"


def download_icon(path: str) -> str:
    url = (
        f"https://github.com/{GITHUB_USER}/"
        f"{GITHUB_REPO}/raw/{GITHUB_BRANCH}/"
        f"{quote(path)}"
    )
    return f"[⬇️]({url})"


# =====================
# Arborescence tree ASCII
# =====================
def tree_prefix(parents_last, is_last):
    prefix = ""
    for last in parents_last[:-1]:
        prefix += "    " if last else "│   "
    if parents_last:
        prefix += "└── " if is_last else "├── "
    return prefix


def walk_tree(root: Path, repo_root: Path, settings, parents_last=None, stl_paths=None):
    if parents_last is None:
        parents_last = []
    if stl_paths is None:
        stl_paths = []

    entries = []
    items = sorted(
        [p for p in root.iterdir() if p.is_dir() or p.suffix.lower() == STL_EXT],
        key=lambda p: (not p.is_dir(), p.name.lower())
    )

    for idx, item in enumerate(items):
        is_last = idx == len(items) - 1
        prefix = tree_prefix(parents_last + [is_last], is_last)

        if item.is_dir():
            entries.append({
                "tree": prefix + item.name,
                "type": "Dossier",
                "perimeters": "",
                "status": "",
                "view": "",
                "download": ""
            })
            entries.extend(
                walk_tree(item, repo_root, settings, parents_last + [is_last], stl_paths)
            )
        else:
            rel_path = item.relative_to(repo_root).as_posix()
            stl_paths.append(rel_path)
            entries.append({
                "tree": prefix + item.name,
                "type": "STL",
                "perimeters": perimeters_value(rel_path, settings),
                "status": status_icon(rel_path, settings),
                "view": view_icon(rel_path),
                "download": download_icon(rel_path)
            })

    return entries


# =====================
# Génération du Markdown
# =====================
def generate_bom(repo_root: Path) -> str:
    settings, settings_path = load_or_create_print_settings(repo_root)
    stl_root = repo_root / STL_DIR

    all_stl_paths = []
    sections = []

    for top in sorted(p for p in stl_root.iterdir() if p.is_dir()):
        sections.append(f"## 📁 `{top.name}`")
        sections.append("")
        sections.append("| Arborescence | Type | Perimeters | Statut | Visualiser | Télécharger |")
        sections.append("|--------------|------|------------|--------|------------|-------------|")
        sections.append(f"| `{top.name}` | Dossier |  |  |  |  |")

        entries = walk_tree(top, repo_root, settings, stl_paths=all_stl_paths)
        for e in entries:
            sections.append(
                f"| `{e['tree']}` | {e['type']} | {e['perimeters']} | "
                f"{e['status']} | {e['view']} | {e['download']} |"
            )
        sections.append("")

    if sync_print_settings(all_stl_paths, settings):
        settings_path.write_text(
            json.dumps(settings, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    header = [
