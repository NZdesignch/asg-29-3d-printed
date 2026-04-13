import os
from pathlib import Path
from collections import defaultdict

STL_DIR = Path("stl")
OUTPUT_FILE = Path("bom.md")
REPO_URL = os.environ.get("REPO_URL", "")


# -----------------------------
# Collect STL files
# -----------------------------
def find_stl_files(root_dir: Path):
    structure = defaultdict(list)
    all_paths = []

    for path in root_dir.rglob("*.stl"):
        if path.is_file():
            relative = path.relative_to(root_dir)

            top_level = relative.parts[0] if len(relative.parts) > 1 else "root"
            structure[top_level].append(relative)

            all_paths.append(relative)

    return structure, all_paths


# -----------------------------
# TREE builder
# -----------------------------
def build_tree(paths):
    tree = {}

    for path in paths:
        node = tree
        for part in path.parts[:-1]:
            node = node.setdefault(part, {})
        node.setdefault("_files", []).append(path.parts[-1])

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
# GitHub link helpers
# -----------------------------
def github_link(path: Path):
    if not REPO_URL:
        return f"`{path.as_posix()}`"
    return f"[{path.name}]({REPO_URL}/blob/main/stl/{path.as_posix()})"


def viewer_link(path: Path):
    if not REPO_URL:
        return ""
    base = REPO_URL.replace("https://github.com", "https://username.github.io")  # à adapter si besoin
    return f"[👁️ 3D]({base}/docs/viewer.html?file=../stl/{path.as_posix()})"


# -----------------------------
# Markdown generation
# -----------------------------
def generate_markdown(structure, all_paths):
    lines = []

    # Title
    lines.append("# 📦 Bill of Materials (STL)\n")

    # TOC
    lines.append("## 📑 Table des matières\n")
    for folder in sorted(structure.keys()):
        anchor = folder.lower().replace(" ", "-")
        lines.append(f"- [{folder}](#{anchor})")
    lines.append("\n---\n")

    # TREE view
    lines.append("## 🌳 Arborescence du dossier STL\n")
    lines.append("```text")
    lines.extend(render_tree(build_tree(all_paths)))
    lines.append("```\n")

    # Tables per folder
    for folder, files in sorted(structure.items()):
        lines.append(f"## 📁 {folder}\n")

        lines.append("| Fichier STL | Lien | 3D |")
        lines.append("|-------------|------|----|")

        for f in sorted(files):
            lines.append(
                f"| {f.name} | {github_link(f)} | {viewer_link(f)} |"
            )

        lines.append("\n")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    if not STL_DIR.exists():
        raise FileNotFoundError("Dossier ./stl introuvable")

    structure, all_paths = find_stl_files(STL_DIR)
    generate_markdown(structure, all_paths)

    print("✔ bom.md généré avec succès")
