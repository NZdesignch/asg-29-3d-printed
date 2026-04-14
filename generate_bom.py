import os
from pathlib import Path

GITHUB_USER = "NZdesignch"
GITHUB_REPO = "asg-29-3d-printedd"
GITHUB_BRANCH = "main"

STL_DIR = "stl"
OUTPUT_MD = "bom.md"
STL_EXT = ".stl"


def github_view_link(path: str) -> str:
    return f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{path}"


def github_download_link(path: str) -> str:
    return f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/raw/{GITHUB_BRANCH}/{path}"


def tree_prefix(level: int) -> str:
    if level <= 1:
        return ""
    return "&nbsp;" * 4 * (level - 2) + "└── "


def analyze_stl(repo_root: Path):
    stl_root = repo_root / STL_DIR
    bom = {}

    for lvl1 in sorted(stl_root.iterdir()):
        if not lvl1.is_dir():
            continue

        rows = []
        base_depth = len(lvl1.parts)

        # Racine du sous-dossier
        rows.append((
            1,
            tree_prefix(1) + lvl1.name,
            "Dossier",
            "",
            ""
        ))

        for current_path, dirs, files in os.walk(lvl1):
            current_path = Path(current_path)
            depth = len(current_path.parts) - base_depth + 1

            if current_path != lvl1:
                rows.append((
                    depth,
                    tree_prefix(depth) + current_path.name,
                    "Dossier",
                    "",
                    ""
                ))

            for f in sorted(files):
                if f.lower().endswith(STL_EXT):
                    rel_path = (current_path / f).relative_to(repo_root).as_posix()
                    rows.append((
                        depth + 1,
                        tree_prefix(depth + 1) + f,
                        "STL",
                        github_view_link(rel_path),
                        github_download_link(rel_path)
                    ))

        if rows:
            bom[lvl1.name] = rows

    return bom


def generate_markdown(bom: dict) -> str:
    md = [
        "# 📦 BOM – ASG‑29 (Pièces imprimées 3D)",
        "",
        f"**Dépôt GitHub** : https://github.com/{GITHUB_USER}/{GITHUB_REPO}",
        "",
        "> Arborescence multi‑niveaux des fichiers STL (un tableau par sous‑ensemble)",
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


def main():
    repo_root = Path(__file__).resolve().parent
    bom_data = analyze_stl(repo_root)
    markdown = generate_markdown(bom_data)

    (repo_root / OUTPUT_MD).write_text(markdown, encoding="utf-8")
    print("✅ bom.md généré avec succès")


if __name__ == "__main__":
    main()
``
