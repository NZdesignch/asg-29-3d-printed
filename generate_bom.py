import os
from pathlib import Path
from collections import defaultdict

STL_DIR = Path("stl")
OUTPUT_FILE = Path("bom.md")
REPO_URL = os.environ.get("REPO_URL", "")


# -----------------------------
# Collect structure
# -----------------------------
def collect_structure(root: Path):
    structure = defaultdict(list)

    for path in root.rglob("*.stl"):
        if path.is_file():
            rel = path.relative_to(root)
            top = rel.parts[0] if len(rel.parts) > 1 else "root"
            structure[top].append(rel)

    return structure


# -----------------------------
# Build hierarchical table rows
# -----------------------------
def build_rows(paths):
    rows = []

    for p in sorted(paths):
        parts = p.parts

        # intermediate folders
        for i in range(len(parts) - 1):
            indent = "  " * i
            rows.append({
                "level": i + 1,
                "name": indent + parts[i] + "/",
                "path": ""
            })

        # file
        rows.append({
            "level": len(parts),
            "name": "  " * (len(parts) - 1) + parts[-1],
            "path": str(p).replace("\\", "/")
        })

    return rows


# -----------------------------
# GitHub link
# -----------------------------
def github_link(path):
    if not REPO_URL:
        return f"`{path}`"
    return f"[{path}]({REPO_URL}/blob/main/stl/{path})"


# -----------------------------
# Markdown generator
# -----------------------------
def generate_md(structure):
    lines = []
    lines.append("# 📦 BOM STL\n")

    for folder, files in sorted(structure.items()):
        lines.append(f"## 📁 {folder}\n")

        lines.append("| Niveau | Élément | Chemin |")
        lines.append("|--------|----------|--------|")

        rows = build_rows(files)

        for r in rows:
            path_display = github_link(r["path"]) if r["path"] else ""
            lines.append(f"| {r['level']} | {r['name']} | {path_display} |")

        lines.append("\n")

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    if not STL_DIR.exists():
        raise FileNotFoundError("Dossier ./stl introuvable")

    structure = collect_structure(STL_DIR)
    generate_md(structure)

    print("✔ bom.md généré en tableau multi-niveaux")
