import os
from pathlib import Path
from collections import defaultdict

REPO_URL = os.environ.get("REPO_URL", "")


# -----------------------------
# Collecte des fichiers STL
# -----------------------------
def find_stl_files(root_dir):
    root_dir = Path(root_dir)
    structure = defaultdict(list)

    all_paths = []

    for path in root_dir.rglob("*.stl"):
        if path.is_file():
            relative = path.relative_to(root_dir)
            structure[relative.parts[0] if len(relative.parts) > 1 else "root"].append(relative)
            all_paths.append(relative)

    return structure, all_paths


# -----------------------------
# Construction arbre TREE
# -----------------------------
def build_tree(paths):
    tree = {}

    for path in paths:
        parts = path.parts
        node = tree

        for part in parts[:-1]:
            node = node.setdefault(part, {})

        node.setdefault("_files", []).append(parts[-1])

    return tree


def render_tree(node, prefix=""):
    lines = []
    entries = list(node.items())

    for i, (name, child) in enumerate(entries):
        is_last = i == len(entries) - 1

        connector = "└── " if is_last else "├── "

        if name == "_files":
            for f in child:
                lines.append(prefix + connector + f)
            continue

        lines.append(prefix + connector + name)

        extension = "    " if is_last else "│   "
        lines.extend(render_tree(child, prefix + extension))

    return lines


# -----------------------------
# Markdown generation
# -----------------------------
def to_github_link(path: Path):
    if not REPO_URL:
        return f"`{path.as_posix()}`"
    return f"[{path.name}]({REPO_URL}/blob/main/{path.as_posix()})"


def generate_markdown(structure, all_paths, output_file):
    lines = []

    # Title
    lines.append("# 📦 Structure des fichiers STL\n")

    # Table des matières
    lines.append("## 📑 Table des matières\n")
    for folder in sorted(structure.keys()):
        anchor = folder.lower().replace(" ", "-")
        lines.append(f"- [{folder}](#{anchor})")
    lines.append("\n---\n")

    # TREE view
    lines.append("## 🌳 Arborescence du projet\n")
    lines.append("```text")
    lines.extend(render_tree(build_tree(all_paths)))
    lines.append("```\n")

    # Sections par dossier
    for folder, files in sorted(structure.items()):
        lines.append(f"## 📁 {folder}\n")

        lines.append("| Fichier STL | Chemin |")
        lines.append("|-------------|--------|")

        for f in sorted(files):
            lines.append(f"| {f.name} | {to_github_link(f)} |")

        lines.append("\n")

    Path(output_file).write_text("\n".join(lines), encoding="utf-8")


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    repo_root = "."
    output_file = "STL_STRUCTURE.md"

    structure, all_paths = find_stl_files(repo_root)
    generate_markdown(structure, all_paths, output_file)

    print(f"Generated {output_file}")
