import json
import urllib.parse
from pathlib import Path
from datetime import datetime

# --- CONFIG ---
GITHUB_USER = "NZdesignch"
GITHUB_REPO = "asg-29-3d-printed"
BRANCH = "main"

OUTPUT_FILE = "bom.md"
SETTINGS_FILE = "print_settings.json"

EXCLUDE = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives', 'previews'}


# --- UTILS ---
def slugify(text):
    return "".join(c for c in text.lower().replace(" ", "-") if c.isalnum() or c in "-_")


def contains_stl(folder: Path):
    return any(folder.rglob("*.stl"))


def load_json():
    try:
        return json.loads(Path(SETTINGS_FILE).read_text(encoding="utf-8"))
    except:
        return {}


def save_json(data):
    Path(SETTINGS_FILE).write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")


# --- WALK HIÉRARCHIQUE PROPRE (IMPORTANT) ---
def walk(folder: Path, root: Path, existing, new_data, md, level=0):
    indent = "&nbsp;" * (level * 4)

    items = sorted(folder.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

    for item in items:
        if any(p in EXCLUDE for p in item.parts):
            continue

        rel = item.relative_to(root).as_posix()

        if item.is_dir():
            if not contains_stl(item):
                continue

            md.append(f"| {indent}📂 **{item.name}** | - | - | - |")

            walk(item, root, existing, new_data, md, level + 1)

        elif item.suffix.lower() == ".stl":

            old = existing.get(rel, {}).get("perimeters")

            new_data[rel] = {"perimeters": old}

            view = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/{BRANCH}/{urllib.parse.quote(rel, safe='/')}"
            raw = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/{urllib.parse.quote(rel, safe='/')}"

            md.append(
                f"| {indent}📄 {item.name} | {'🟢' if old else '🔴'} | "
                f"{old or '---'} | [🔍]({view}) / [💾]({raw}) |"
            )


# --- MAIN ---
def generate_bom():
    root = Path(".")

    existing = load_json()
    new_data = existing.copy()

    md = []
    md.append("# 📋 Nomenclature (BOM)")
    md.append(f"_Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n")

    md += [
        "| Fichier / Structure | État | Périmètres | Actions |",
        "| :--- | :---: | :---: | :--- |"
    ]

    # scan racines
    for folder in sorted(root.iterdir()):
        if not folder.is_dir():
            continue
        if folder.name in EXCLUDE:
            continue
        if not contains_stl(folder):
            continue

        md.append(f"| 📦 **{folder.name}** | - | - | - |")
        walk(folder, root, existing, new_data, md, 1)

    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    save_json(new_data)

    print("✅ BOM réparé (tableaux conservés)")


if __name__ == "__main__":
    generate_bom()
