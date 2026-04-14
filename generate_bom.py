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

REQUIRED_PRINT_KEYS = ["material", "layer_height", "infill"]


# =====================
# Chargement paramètres impression
# =====================
def load_print_settings(repo_root: Path) -> dict:
    path = repo_root / PRINT_SETTINGS_FILE
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def print_status_icon(rel_path: str, settings: dict) -> str:
    if rel_path not in settings:
        return "🔴"

    data = settings[rel_path]
    if all(k in data for k in REQUIRED_PRINT_KEYS):
        return "🟢"

    return "🟡"


# =====================
# Liens GitHub encodés
# =====================
def view_icon(path: str) -> str:
    return f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{quote(path)}"


def download_icon(path: str) -> str:
    return f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/raw/{GITHUB_BRANCH}/{quote(path)}"


# =====================
# Arborescence tree
# =====================
def tree_prefix(parents_last, is_last):
    prefix = ""
    for last in parents_last[:-1]:
        prefix += "    " if last else "│   "
    if parents_last:
        prefix += "└── " if is_last else "├── "
    return prefix


def walk_tree(root: Path, repo_root: Path, print_settings: dict, parents_last=None):
    if parents_last is None:
        parents_last = []

    entries = []

    items = sorted(
        [p for p in root.iterdir() if p.is_dir() or p.suffix.lower() == STL_EXT],
        key=lambda p: (not p.is_dir(), p.name.lower())
    )

    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        prefix = tree_prefix(parents_last + [is_last], is_last)

        if item.is_dir():
            entries.append({
                "tree": prefix + item.name,
                "type": "Dossier",
                "status": "",
                "view": "",
                "download": ""
            })
            entries.extend(
                walk_tree(item, repo_root, print_settings, parents_last + [is_last])
            )
        else:
            rel_path = item.relative_to(repo_root).as_posix()
            entries.append({
                "tree": prefix + item.name,
                "type": "STL",
                "status": print_status_icon(rel_path, print_settings),
                "view": view_icon(rel_path),
                "download": download_icon(rel_path)
            })

    return entries


# =====================
# Génération Markdown
# =====================
def generate_markdown(repo_root: Path) -> str:
    stl_root = repo_root / STL_DIR
    print_settings = load_print_settings(repo_root)

    lines = [
        "# 📦 BOM – ASG‑29 (Pièces imprimées 3D)",
        "",
        f"Dépôt GitHub : https://github.com/{GITHUB_USER}/{GITHUB_REPO}",
        "",
        "🟢 Paramètres impression OK 🟡 Incomplet 🔴 Manquant",
        "",
        "---",
        ""
    ]

    for top_dir in sorted(p for p in stl_root.iterdir() if p.is_dir()):
        lines.append(f"## 📁 `{top_dir.name}`")
        lines.append("")
        lines.append("| Arborescence | Type | Impression | Visualiser | Télécharger |")
        lines.append("|--------------|------|------------|------------|-------------|")
        lines.append(f"| `{top_dir.name}` | Dossier |  |  |  |")

        for e in walk_tree(top_dir, repo_root, print_settings):
            lines.append(
                f"| `{e['tree']}` | {e['type']} | {e['status']} | {e['view']} | {e['download']} |"
            )

        lines.append("")

    return "\n".join(lines)


# =====================
# Main
# =====================
def main():
    repo_root = Path(__file__).resolve().parent
    (repo_root / OUTPUT_MD).write_text(
        generate_markdown(repo_root),
        encoding="utf-8"
    )
    print("✅ bom.md généré avec statut des paramètres d'impression")


if __name__ == "__main__":
    main()
