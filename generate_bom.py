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


def tree_prefix(level: int) -> str:
    if level <= 1:
        return ""
    return "    " * (level - 2) + "└── "


def analyze_stl(repo_root: Path):
    stl_root = repo_root / STL_DIR
    bom = {}

    if not stl_root.exists():
        return bom

    for top_dir in sorted(stl_root.iterdir()):
        if not top_dir.is_dir():
            continue

        rows = []
        base_depth = len(top_dir.parts)

        rows.append({
            "level": 1,
            "tree": top_dir.name,
            "type": "Dossier",
            "view": "",
            "download": ""
        })

        for current_path, dirs, files in os.walk(top_dir):
            current_path = Path(current_path)
