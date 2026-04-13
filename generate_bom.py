import os
from pathlib import Path

def scan_tree(root: Path, base_url: str, raw_url: str, prefix=""):
    """
    Retourne une liste de lignes représentant l'arborescence en mode tree.
    """
    entries = sorted(list(root.iterdir()))
    rows = []

    for i, item in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        subtree_prefix = "    " if i == len(entries) - 1 else "│   "

        if item.is_dir():
            rows.append({
                "type": "folder",
                "tree": prefix + connector + f"{item.name}/",
                "view": "",
                "download": "",
                "name": f"📁 {item.name}/"
            })
            rows.extend(scan_tree(item, base_url, raw_url, prefix + subtree_prefix))

        elif item.suffix.lower() == ".stl":
            relative_path = item.as_posix()

            rows.append({
                "type": "file",
                "tree": prefix + connector,
                "view": f"[👁️]({base_url}/{relative_path})",
                "download": f"[⬇️]({raw_url}/{relative_path})",
                "name": item.name
            })

    return rows


def generate_bom(stl_folder: str, output_file: str):
    root = Path(stl_folder)
    if not root.exists():
        raise FileNotFoundError(f"Le dossier '{stl_folder}' est introuvable.")

    # Récupération automatique du user et repo depuis GitHub Actions
    repo_full = os.environ.get("GITHUB_REPOSITORY", "unknown/unknown")
    user, repo = repo_full.split("/") if "/" in repo_full else ("unknown", "unknown")

    base_url = f"https://github.com/{user}/{repo}/blob/main/{stl_folder}"
    raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/main/{stl_folder}"

    md = f"# Bill of Materials (STL)\n"
    md += f"**Dépôt :** https://github.com/{user}/{repo}\n\n"
    md += "## 📦 Nomenclature par dossier de premier niveau\n\n"

    # Dossiers de premier niveau
    for item in sorted(root.iterdir()):
        if item.is_dir():
            md += f"### 📁 {item.name}\n\n"
            md += "| Nom | Voir | Télécharger | Arborescence |\n"
            md += "|-----|------|-------------|--------------|\n"

            rows = scan_tree(item, base_url, raw_url)

            for r in rows:
                md += (
                    f"| {r['name']} "
                    f"| {r['view']} "
                    f"| {r['download']} "
                    f"| `{r['tree']}` |\n"
                )

            md += "\n"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md)

    print(f\"Fichier '{output_file}' généré avec succès.\")


if __name__ == "__main__":
    STL_FOLDER = "stl"
    OUTPUT_MD = "bom.md"

    generate_bom(STL_FOLDER, OUTPUT_MD)
