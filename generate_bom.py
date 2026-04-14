import os
from pathlib import Path

# =====================
# Configuration GitHub
# =====================
GITHUB_USER = "NZdesignch"
GITHUB_REPO = "asg-29-3d-printedd"
GITHUB_BRANCH = "main"

# =====================
# Configuration projet
# =====================
STL_DIR = "stl"
OUTPUT_MD = "bom.md"
STL_EXT = ".stl"


def github_view_link(path: str) -> str:
    url = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{path}"
    return f"[🔍]({url})"


def github_download_link(path: str) -> str:
    url = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/raw/{GITHUB_BRANCH}/{path}"
    return f"[⬇️]({url})"


def build_tree_prefix(depth: int, is_last: bool, parents_last):
    prefix = ""
    for last in parents_last[:-1]:
        prefix += "    " if last else "│   "

    if depth > 0:
        prefix += "└── " if is_last else "├── "

    return prefix


def walk_tree(root: Path, repo_root: Path, depth=0, parents_last=[]):
    entries = []
    items = sorted([p for p in root.iterdir() if p.is_dir() or p.suffix.lower() == STL_EXT])
    count = len(items)

    for index, item in enumerate(items):
        is_last = index == count - 1
        prefix = build_tree_prefix(depth, is_last, parents_last)

        if item.is_dir():
            entries.append({
                "tree": prefix + item.name,
                "type": "Dossier",
                "view": "",
                "download": ""
            })
            entries.extend(
                walk_tree(item, repo_root, depth + 1, parents_last + [is_last])
            )
        else:
            rel_path = item.relative_to(repo_root).as_posix()
            entries.append({
                "tree": prefix + item.name,
                "type": "STL",
                "view": github_view_link(rel_path),
                "download": github_download_link(rel_path)
            })

    return entries


def analyze_stl(repo_root: Path):
    stl_root = repo_root / STL_DIR
    bom = {}

    if not stl_root.exists():
        return bom

    for top_dir in sorted(p for p in stl_root.iterdir() if p.is_dir()):
        rows = [{
            "tree": top_dir.name,
            "type": "Dossier",
            "view": "",
            "download": ""
        }]

        rows.extend(walk_tree(top_dir, repo_root))
        bom[top_dir.name] = rows

    return bom


def generate_markdown(bom: dict) -> str:
    md = [
        "# 📦 BOM – ASG‑29 (Pièces imprimées 3D)",
        "",
        f"**Dépôt GitHub** : https://github.com/{GITHUB_USER}/{GITHUB_REPO}",
        "",
        "> Nomenclature multi‑niveaux – affichage arborescent",
        "",
        "---",
        ""
    ]

    for section, rows in bom.items():
        md.append(f"## 📁 `{section}`")
        md.append("")
        md.append("| Arborescence | Type | Visualiser | Télécharger |")
        md.append("|--------------|------|------------|-------------|")

        for r in rows:
            md.append(
