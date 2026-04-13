import os
from pathlib import Path

def build_tree(root: Path):
    """
    Construit une structure hiérarchique représentant les dossiers et fichiers STL.
    Format :
    {
        "files": ["piece1.stl", "piece2.stl"],
        "subfolder": { ... }
    }
    """
    tree = {"files": []}

    for item in sorted(root.iterdir()):
        if item.is_dir():
            tree[item.name] = build_tree(item)
        elif item.suffix.lower() == ".stl":
            tree["files"].append(item.name)

    return tree


def tree_to_markdown(tree: dict, level: int = 0):
    """
    Convertit la structure hiérarchique en Markdown multi-niveaux.
    """
    md = ""
    indent = "  " * level

    # Fichiers STL du dossier courant
    for f in tree.get("files", []):
        md += f"{indent}- **{f}**\n"

    # Sous-dossiers
    for key, value in tree.items():
        if key == "files":
            continue
        md += f"{indent}- {key}/\n"
        md += tree_to_markdown(value, level + 1)

    return md


def generate_md(stl_root: str, output_file: str, user: str, repo: str):
    """
    Génère le fichier Markdown final.
    """
    root = Path(stl_root)
    if not root.exists():
        raise FileNotFoundError(f"Le dossier STL '{stl_root}' est introuvable.")

    tree = build_tree(root)

    md = f"# Nomenclature des fichiers STL\n"
    md += f"**Dépôt :** https://github.com/{user}/{repo}\n\n"
    md += tree_to_markdown(tree)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Nomenclature générée dans {output_file}")


if __name__ == "__main__":
    # Variables d'environnement fournies par GitHub Actions
    GITHUB_USER = os.environ.get("GITHUB_USER", "unknown-user")
    GITHUB_REPO = os.environ.get("GITHUB_REPO", "unknown-repo")

    # Dossier contenant les STL (relatif à la racine du dépôt)
    STL_FOLDER = "stl"  # adapte si nécessaire
    OUTPUT_MD = "bom.md"

    generate_md(STL_FOLDER, OUTPUT_MD, GITHUB_USER, GITHUB_REPO)
