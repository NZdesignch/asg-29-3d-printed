import os
from pathlib import Path

def build_tree(root: Path):
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

    for f in tree.get("files", []):
        md += f"{indent}- **{f}**\n"

    for key, value in tree.items():
        if key == "files":
            continue
        md += f"{indent}- {key}/\n"
        md += tree_to_markdown(value, level + 1)

    return md


def generate_md(stl_root: str, output_file: str, user: str, repo: str):
    root = Path(stl_root)
    tree = build_tree(root)

    md = f"# Nomenclature des fichiers STL\n"
    md += f"**Dépôt :** https://github.com/{user}/{repo}\n\n"
    md += tree_to_markdown(tree)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"Nomenclature générée dans {output_file}")


if __name__ == "__main__":
    # Variables d'environnement
    GITHUB_USER = os.environ.get
