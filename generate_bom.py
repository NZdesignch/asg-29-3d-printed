import os
from pathlib import Path

IGNORED_DIRS = {".git", ".github", "__pycache__", ".vscode"}

def build_tree(root: Path, base_url: str):
    tree = {"files": []}

    for item in sorted(root.iterdir()):
        if item.name in IGNORED_DIRS:
            continue

        if item.is_dir():
            subtree = build_tree(item, base_url)
            # On n'ajoute le dossier que s'il contient des STL ou sous-dossiers utiles
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
    md = ""
    indent = "  " * level

    for f in tree.get("files", []):
        md += f"{indent}- **[{f['name']}]({f['url']})**\n"

    for key, value in tree.items():
        if key == "files":
            continue
        md += f"{indent}- {key}/\n"
        md += tree_to_markdown(value, level + 1)

    return md


def generate_md(root_folder: str, output_file: str, user: str, repo: str):
    root = Path(root_folder)
    base_url = f"https://github.com/{user}/{repo}/blob/main"

    tree = build_tree(root, base_url)

    md = f"# Nomenclature des fichiers STL\n"
    md += f"**Dépôt :** https://github.com/{user}/{repo}\n\n"
    md += tree_to_markdown(tree)

    # Toujours créer le fichier, même vide
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"NOMENCLATURE.md généré avec succès.")


if __name__ == "__main__":
    GITHUB_USER = os.environ.get("GITHUB_USER", "unknown-user")
    GITHUB_REPO = os.environ.get("GITHUB_REPO", "unknown-repo")

    ROOT_FOLDER = "."          # On scanne tout le dépôt
    OUTPUT_MD = "NOMENCLATURE.md"

    generate_md(ROOT_FOLDER, OUTPUT_MD, GITHUB_USER, GITHUB_REPO)
