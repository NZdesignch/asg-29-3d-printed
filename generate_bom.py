import os
from pathlib import Path
import subprocess

def clone_or_update_repo(repo_url: str, local_path: str):
    local = Path(local_path)

    if not local.exists():
        print(f"Clonage du dépôt dans {local_path}")
        subprocess.run(["git", "clone", repo_url, local_path], check=True)
    else:
        print(f"Mise à jour du dépôt dans {local_path}")
        subprocess.run(["git", "-C", local_path, "pull"], check=True)


def build_tree(root: Path):
    """
    Construit une structure hiérarchique :
    { dossier: { sous_dossier: {...}, "files": [liste STL] } }
    """
    tree = {"files": []}

    for item in sorted(root.iterdir()):
        if item.is_dir():
            tree[item.name] = build_tree(item)
        elif item.suffix.lower() == ".stl":
            tree["files"].append(item.name)

    return tree


def tree_to_markdown(tree: dict, level: int = 0):
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


def generate_md(repo_path: str, stl_root: str, output_file: str):
    root = Path(repo_path) / stl_root
    tree = build_tree(root)
    md_content = "# Nomenclature des fichiers STL\n\n" + tree_to_markdown(tree)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Nomenclature générée dans {output_file}")


if __name__ == "__main__":
    # 🔧 Paramètres à adapter
    GITHUB_REPO = "https://github.com/ton-utilisateur/ton-depot.git"
    LOCAL_REPO_PATH = "./repo_local"
    STL_FOLDER = "chemin/vers/dossier/stl"  # relatif au dépôt
    OUTPUT_MD = "NOMENCLATURE.md"

    clone_or_update_repo(GITHUB_REPO, LOCAL_REPO_PATH)
    generate_md(LOCAL_REPO_PATH, STL_FOLDER, OUTPUT_MD)
