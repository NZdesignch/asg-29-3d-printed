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
    url = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{encoded}"
    return f"[🔍]({url})"


def github_download_link(path: str) -> str:
    encoded = quote(path)
    url = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/raw/{GITHUB_BRANCH}/{encoded}"
    return f"[⬇️]({url})"


# =====================
# Construction du tree
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

    items = sorted(
        [p for p in root.iterdir() if p.is_dir() or p.suffix.lower() == STL_EXT],
        key=lambda p: (not p.is_dir(), p.name.lower())
    )

    for idx, item in enumerate(items):
        is_last = idx == len(items) - 1
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


# =====================
# Génération Markdown
# =====================
def generate_markdown(repo_root: Path) -> str:
    stl_root = repo_root / STL_DIR

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

    if not stl_root.exists():
        md.append("_Aucun dossier `stl/` trouvé._")
        return "\n".join(md)

    for top_dir in sorted(p for p in stl_root.iterdir() if p.is_dir()):
        md.append(f"## 📁 `{top_dir.name}`")
        md.append("")
        md.append("| Arborescence | Type | Visualiser | Télécharger |")
        md.append("|--------------|------|------------|-------------|")

        # Racine du sous-ensemble
        md.append(f"| `{top_dir.name}` | Dossier |  |  |")

        for r in walk_tree(top_dir, repo_root):
            md.append(
                f"| `{r['tree']}` | {r['type']} | {r['view']} | {r['download']} |"
            )

        md.append("")

    return "\n".join(md)


# =====================
# Main
# =====================
def main():
    repo_root = Path(__file__).resolve().parent
    markdown = generate_markdown(repo_root)

    output_file = repo_root / OUTPUT_MD
    output_file.write_text(markdown, encoding="utf-8")

    print("✅ bom.md généré – tree clair, liens encodés et masqués")


if __name__ == "__main__":
    main()
``
