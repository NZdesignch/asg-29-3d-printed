import os
from pathlib import Path

def scan_stl_tree(root: Path, base_url: str):
    """
    Parcourt récursivement tous les sous-dossiers du dossier stl/
    et construit une structure hiérarchique.
    """
    tree = {"files": []}

    for item in sorted(root.iterdir()):
        if item.is_dir():
            subtree = scan_stl_tree(item, base_url)
            if subtree["files"] or any(k != "files" for k in subtree):
                tree[item.name] = subtree

        elif item.suffix.lower() == ".stl":
            relative_path = item.as_posix()
            tree["files"].append({
                "name": item.name,
                "url": f"{base_url}/{relative_path}"
            })

    return tree


def tree_to_markdown(tree: dict, level: int = 0):
    """
    Convertit la structure hiérarchique en Markdown multi-niveaux.
    """
    md = ""
    indent = "  " * level

    # Fichiers STL
    for f in tree.get("files", []):
        md += f"{indent}- **[{f['name']}]({f['url']})**\n"

    # Sous-dossiers
    for key, value in tree.items():
        if key == "files":
            continue
        md += f"{indent}- {key}/\n"
        md += tree_to_markdown(value, level + 1)

    return md


def generate_bom(stl_folder: str, output_file: str, user: str, repo: str):
    """
    Génère bom.md à partir du dossier stl/.
    """
    root = Path(stl_folder)
    if not root.exists():
        raise FileNotFoundError(f"Le dossier '{stl_folder}' est introuvable.")

    base_url = f"https://github.com/{user}/{repo}/blob/main/{stl_folder}"

    tree = scan_stl_tree(root, base_url)

    md = f"# Bill of Materials (STL)\n"
    md += f"**Dépôt :**
