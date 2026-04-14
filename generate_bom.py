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
            parts[rel_path].setdefault("perimeters", None)

    return updated


def perimeters_status(rel_path: str, settings: dict) -> str:
    part = settings["parts"].get(rel_path)
    if part is None:
        return "🔴"
    if part.get("perimeters") is not None:
        return "🟢"
    return "🟡"


# =====================
# Liens GitHub (icônes)
# =====================
def view_icon(path: str) -> str:
    return f"[🔍](https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{quote(path)})"


def download_icon(path: str) -> str:
    return f"[⬇️](https://github.com/{GITHUB_USER}/{GITHUB_REPO}/raw/{GITHUB_BRANCH}/{quote(path)})"


# =====================
# Construction arbre ASCII
# =====================
def tree_prefix(parents_last, is_last):
    prefix = ""
    for last in parents_last[:-1]:
        prefix += "    " if last else "│   "
    if parents_last:
        prefix += "└── " if is_last else "├── "
    return prefix


def walk_tree(root: Path, repo_root: Path, settings: dict, parents_last=None, stl_paths=None):
    if parents_last is None:
        parents_last = []
    if stl_paths is None:
        stl_paths = []

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
                walk_tree(item, repo_root, settings, parents_last + [is_last], stl_paths)
            )
        else:
            rel_path = item.relative_to(repo_root).as_posix()
            stl_paths.append(rel_path)
            entries.append({
                "tree": prefix + item.name,
                "type": "STL",
                "status": perimeters_status(rel_path, settings),
                "view": view_icon(rel_path),
                "download": download_icon(rel_path)
            })

    return entries


# =====================
# Génération BOM
# =====================
def generate_bom(repo_root: Path) -> str:
    stl_root = repo_root / STL_DIR
    settings, settings_path = load_or_create_print_settings(repo_root)

    all_stl_paths = []
    sections = []

    for top in sorted(p for p in stl_root.iterdir() if p.is_dir()):
        section = []
        section.append(f"## 📁 `{top.name}`")
        section.append("")
        section.append("| Arborescence | Type | Perimeters | Visualiser | Télécharger |")
        section.append("|--------------|------|------------|------------|-------------|")
        section.append(f"| `{top.name}` | Dossier |  |  |  |")

        entries = walk_tree(top, repo_root, settings, stl_paths=all_stl_paths)

        for e in entries:
            section.append(
                f"| `{e['tree']}` | {e['type']} | {e['status']} | {e['view']} | {e['download']} |"
            )

        section.append("")
        sections.extend(section)

    updated = sync_print_settings(all_stl_paths, settings)
    if updated:
        settings_path.write_text(
            json.dumps(settings, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    header = [
        "# 📦 BOM – ASG‑29 (Pièces imprimées 3D)",
        "",
        f"Dépôt GitHub : https://github.com/{GITHUB_USER}/{GITHUB_REPO}",
        "",
        "🟢 perimeters défini 🟡 à définir 🔴 absent",
        "",
        "---",
        ""
    ]

    if settings["global"]:
        header.append("## ⚙️ Paramètres d’impression globaux")
        for k, v in settings["global"].items():
            header.append(f"- **{k}** : {v}")
        header.append("")
        header.append("---")
        header.append("")

    return "\n".join(header + sections)


# =====================
# Main
# =====================
def main():
    repo_root = Path(__file__).resolve().parent
    bom_md = generate_bom(repo_root)
    (repo_root / OUTPUT_MD).write_text(bom_md, encoding="utf-8")
    print("✅ bom.md généré et print_settings.json synchronisé")


if __name__ == "__main__":
    main()
``
