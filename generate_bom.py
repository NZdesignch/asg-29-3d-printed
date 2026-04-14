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
# Liens GitHub
# =====================
def github_view_link(path: str) -> str:
    return f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{path}"

def github_download_link(path: str) -> str:
    return f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/raw/{GITHUB_BRANCH}/{path}"


# =====================
# Tree prefix Markdown
# =====================
def tree_prefix(level: int) -> str:
    if level <= 1:
        return ""
    return "&nbsp;" * 4 * (level - 2) + "└── "


# =====================
# Analyse des STL
# =====================
def analyze_stl(repo_root: Path):
    stl_root = repo_root / STL_DIR
    bom = {}

    if not stl_root.exists():
        return bom

    for level1_dir in sorted(stl_root.iterdir()):
        if not level1_dir.is_dir():
            continue

        rows = []
        base_depth = len(level1_dir.parts)

        # Racine du sous-ensemble
        rows.append((
            1,
            tree_prefix(1) + level1_dir.name,
            "Dossier",
            "",
            ""
        ))

        for current_path, dirs, files in os.walk(level1_dir):
            current_path = Path(current_path)
            depth = len(current_path.parts) - base_depth + 1

            if current_path != level1_dir:
                rows.append((
                    depth,
                    tree_prefix(depth) + current_path.name,
                    "Dossier",
                    "",
                    ""
                ))

            for file in sorted(files):
                if file.lower().endswith(STL_EXT):
                    rel_path = (current_path / file).relative_to(repo_root).as_posix()
                    rows.append((
                        depth + 1,
                        tree_prefix(depth + 1) + file,
                        "STL",
                        github_view_link(rel_path),
                        github_download_link(rel_path)
                    ))

        if rows:
            bom[level1_dir.name] = rows

    return bom


# =====================
# Génération Markdown
# =====================
def generate_markdown(bom: dict) -> str:
    md = [
        "# 📦 BOM – ASG‑29 (Pièces imprimées 3D)",
        "",
        f"**Dépôt GitHub** : https://github.com/{GITHUB_USER}/{GITHUB_REPO}",
        "",
        "> Nomenclature des fichiers STL – arborescence multi‑niveaux",
        "",
        "---",
        ""
    ]

    for section, rows in bom.items():
        md.append(f"## 📁 `{section}`")
        md.append("")
        md.append("| Arborescence | Type | Visualiser | Télécharger |")
        md.append("|-------------|------|------------|-------------|")

        for _, name, kind, view, download in rows:
            view_link = f"[👁️ Voir]({view})" if view else ""
            download_link = f"[⬇️ STL]({download})" if download else ""
            md.append(f"| {name} | {kind} | {view_link} | {download_link} |")

        md.append("")

    return "\n".join(md)


# =====================
# Main
# =====================
def main():
    repo_root = Path(__file__).resolve().parent
    bom_data = analyze_stl(repo_root)
    markdown = generate_markdown(bom_data)

    output_file = repo_root / OUTPUT_MD
    output_file.write_text(markdown, encoding="utf-8")

    print("✅ bom.md généré avec succès")


if __name__ == "__main__":
    main()
