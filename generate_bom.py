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


def tree_to_table(tree: dict, parent: str = ""):
    """
    Convertit la structure hiérarchique en lignes de tableau Markdown.
    """
    rows = []

    # Fichiers STL
    for f in tree.get("files", []):
        rows.append(f"| 🧩 Fichier | {parent} | **[{f['name']}]({f['url']})** |")

    # Sous-dossiers
    for key, value in tree.items():
        if key == "files":
            continue
        folder_path = f"{parent}/{key}" if parent else key
        rows.append(f"| 📁 Dossier | {parent if parent else '/'} | **{key}/** |")
        rows.extend(tree_to_table(value, folder_path))

    return rows


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
    md += f"**Dépôt :** https://github.com/{user}/{repo}\n\n"

    md += "## 📦 Nomenclature complète\n\n"
    md += "| Type |
