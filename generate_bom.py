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
    return f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{path}"


def github_download_link(path: str) -> str:
    return f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/raw/{GITHUB_BRANCH}/{path}"


def tree_prefix(level: int) -> str:
    """Indentation lisible pour Markdown (monospace)"""
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

        # Niveau 1
        rows.append({
            "level": 1,
            "tree": top_dir.name,
            "type": "Dossier",
            "view": "",
            "download": ""
        })

        for current_path, dirs, files in os.walk(top_dir):
            current_path = Path(current_path)
            depth = len(current_path.parts) - base_depth + 1

            if current_path != top_dir:
                rows.append({
                    "level": depth,
                    "tree": tree_prefix(depth) + current_path.name,
                    "type": "Dossier",
                    "view": "",
                    "download": ""
                })

            for f in sorted(files):
                if f.lower().endswith(STL_EXT):
                    rel_path = (current_path / f).relative_to(repo_root).as_posix()
                    rows.append({
                        "level": depth + 1,
                        "tree": tree_prefix(depth + 1) + f,
                        "type": "STL",
                        "view": github_view_link(rel_path),
                        "download": github_download_link(rel_path)
                    })

        bom[top_dir.name] = rows

    return bom


def generate_markdown(bom: dict) -> str:
    md = [
        "# 📦 BOM – ASG‑29 (Pièces imprimées 3D)",
        "",
        f"**Dépôt GitHub** : https://github.com/{GITHUB_USER}/{GITHUB_REPO}",
        "",
        "> Nomenclature multi‑niveaux des fichiers STL",
        "",
        "---",
        ""
    ]

    for section, rows in bom.items():
        md.append(f"## 📁 `{section}`")
        md.append("")
        md.append("| Niveau | Arborescence | Type | Visualiser | Télécharger |")
        md.append("|------:|--------------|------|------------|-------------|")

        for r in rows:
            view = f"[🔍]({r['view']})" if r["view"] else ""
            download = f"[⬇️]({r['download']})" if r["download"] else ""

            md.append(
                f"| {r['level']} "
                f"| `{r['tree']}` "
                f"| {r['type']} "
                f"| {view} "
                f"| {download} |"
            )

        md.append("")

    return "\n".join(md)


def main():
    repo_root = Path(__file__).resolve().parent
    bom_data = analyze_stl(repo_root)

    output_file = repo_root / OUTPUT_MD
    output_file.write_text(generate_markdown(bom_data), encoding="utf-8")

    print("✅ bom.md généré avec succès")


if __name__ == "__main__":
    main()
