import os
from pathlib import Path
from urllib.parse import quote

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
# Liens GitHub (URL encodées)
# =====================
def github_view_link(path: str) -> str:
    encoded = quote(path)
    return (
        "https://github.com/"
        + GITHUB_USER
        + "/"
        + GITHUB_REPO
        + "/blob/"
        + GITHUB_BRANCH
        + "/"
        + encoded
    )


def github_download_link(path: str) -> str:
    encoded = quote(path)
    return (
        "https://github.com/"
        + GITHUB_USER
        + "/"
        + GITHUB_REPO
        + "/raw/"
        + GITHUB_BRANCH
        + "/"
        + encoded
    )


# =====================
# Construction du tree
# =====================
def build_tree_prefix(parents_last, is_last):
    prefix = ""
    for last in parents_last[:-1]:
        prefix += "    " if last else "│   "
    if parents_last:
        prefix += "└── " if is_last else "├── "
    return prefix


def walk_tree(root: Path, repo_root: Path, parents_last=None):
    if parents_last is None:
        parents_last = []

    entries = []

    items = sorted(
        [p for p in root.iterdir() if p.is_dir() or p.suffix.lower() == STL_EXT],
        key=lambda p: (not p.is_dir(), p.name.lower())
    )

    total = len(items)

    for index, item in enumerate(items):
        is_last = index == total - 1
        prefix = build_tree_prefix(parents_last + [is_last], is_last)

        if item.is_dir():
            entries.append({
                "tree": prefix + item.name,
                "type": "Dossier",
                "view": "",
                "download": ""
            })
            entries.extend(
                walk_tree(item, repo_root, parents_last + [is_last])
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


# =====================
# Génération Markdown
# =====================
def generate_markdown(repo_root: Path) -> str:
    stl_root = repo_root / STL_DIR

    lines = [
        "# 📦 BOM – ASG‑29 (Pièces imprimées 3D)",
        "",
        "Dépôt GitHub : https://github.com/"
        + GITHUB_USER
        + "/"
        + GITHUB_REPO,
        "",
        "---",
        ""
    ]

    if not stl_root.exists():
        lines.append("_Aucun dossier stl/ trouvé._")
        return "\n".join(lines)

    for top_dir in sorted(p for p in stl_root.iterdir() if p.is_dir()):
        lines.append("## 📁 `" + top_dir.name + "`")
        lines.append("")
        lines.append("| Arborescence | Type | Visualiser | Télécharger |")
        lines.append("|--------------|------|------------|-------------|")
        lines.append("| `" + top_dir.name + "` | Dossier |  |  |")

        for entry in walk_tree(top_dir, repo_root):
            lines.append(
                "| `"
                + entry["tree"]
                + "` | "
                + entry["type"]
                + " | "
                + entry["view"]
                + " | "
                + entry["download"]
                + " |"
            )

        lines.append("")

    return "\n".join(lines)


# =====================
# Main
# =====================
def main():
    repo_root = Path(__file__).resolve().parent
    markdown = generate_markdown(repo_root)
    output_path = repo_root / OUTPUT_MD
    output_path.write_text(markdown, encoding="utf-8")
    print("✅ bom.md généré avec succès")


if __name__ == "__main__":
    main()
