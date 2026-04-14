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


def md_view_link(path: str) -> str:
    url = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{path}"
    return f"[🔍]({url})"


def md_download_link(path: str) -> str:
    url = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/raw/{GITHUB_BRANCH}/{path}"
    return f"[⬇️]({url})"


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
    items = sorted(
        [p for p in root.iterdir() if p.is_dir() or p.suffix.lower() == STL_EXT],
        key=lambda p: (not p.is_dir(), p.name.lower())
    )

    for idx, item in enumerate(items):
        is_last = idx == len(items) - 1
