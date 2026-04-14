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


# =====================
# Liens GitHub (masqués)
# =====================
def github_view_link(path: str) -> str:
    url = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{path}"
    return f"[🔍]({url})"

def github_download_link(path: str) -> str:
    url = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/raw/{GITHUB_BRANCH}/{path}"
    return f"[⬇️]({url})"


# =====================
# Construction arbre
# =====================
def build_tree_prefix(depth: int, is_last: bool, parents_last):
    prefix = ""
    for last in parents_last:
        prefix += "    " if last else "│   "

    if depth > 0:
        prefix += "└── " if is_last else "├── "

    return prefix


def walk_tree(root: Path, repo_root: Path, depth=0, parents_last=None):
    if parents_last is None:
        parents_last = []

    entries = []

    # Dossiers + STL uniquement
    items = sorted(
        [p for p in root.iterdir() if p.is_dir() or p.suffix.lower() == STL_EXT],
        key=lambda p: (not p.is_dir(), p.name.lower())
    )

    count = len(items)

    for idx, item in enumerate(items):
        is_last = idx == count - 1
        prefix = build_tree_prefix(depth, is_last, parents_last)

        if item.is_dir():
            entries.append({
                "tree": prefix + item.name,
                "type": "Dossier",
                "view": "",
                "download": ""
            })

            entries.extend(
                walk_tree(
                    item,
                    repo_root,
