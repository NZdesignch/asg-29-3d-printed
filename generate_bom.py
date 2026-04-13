import json
import shutil
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
COMMON_KEYS = ["top_solid_layers", "bottom_solid_layers", "fill_density", "fill_pattern"]


# --- UTILS ---
def slugify(text):
    text = text.lower().strip().replace(" ", "-")
    return "".join(c for c in text if c.isalnum() or c in "-_")


def load_json():
    if Path(SETTINGS_FILE).exists():
        try:
            return json.loads(Path(SETTINGS_FILE).read_text(encoding="utf-8"))
        except:
            print("⚠️ JSON corrompu")
    return {}


def save_json(data):
    Path(SETTINGS_FILE).write_text(
        json.dumps(data, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )


def contains_stl(folder):
    return any(folder.rglob("*.stl"))


def file_size_kb(path):
    return round(path.stat().st_size / 1024, 1)


# --- 🌳 PARCOURS HIÉRARCHIQUE ---
def walk_tree(folder, root, existing_data, new_data, md, level=0):
    indent = "&nbsp;" * 6 * level

    # Nom dossier
    if level == 0:
        md.append(f"\n## 📂 {folder.name}")
    else:
        md.append(f"| {indent}📂 **{folder.name}** | - | - | - | - |")

    items = sorted(folder.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))

    for item in items:
        if any(part in EXCLUDE for part in item.parts):
            continue

        if item.is_dir():
            if contains_stl(item):  # on ignore les dossiers vides de STL
                walk_tree(item, root, existing_data, new_data, md, level + 1)
            continue

        if item.suffix.lower() != ".stl":
            continue

        rel = item.relative_to(root).as_posix()
        encoded = urllib.parse.quote(rel, safe='/')

        old_val = existing_data.get(rel, {}).get("perimeters")

        if rel not in new_data:
            new_data[rel] = {"perimeters": old_val}

        size = file_size_kb(item)

        view = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/{BRANCH}/{encoded}"
        raw = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/{encoded}"
        viewer = f"https://3dviewer.net/#model={raw}"

        md.append(
            f"| {indent}&nbsp;&nbsp;📄 {item.name} | "
            f"{'🟢' if old_val else '🔴'} | "
            f"{old_val or '---'} | "
            f"{size} KB | "
            f"[🔍]({view}) [💾]({raw}) [🧊]({viewer}) |"
        )


# --- MAIN ---
def generate_bom():
    root = Path(".")
    arc_dir = root / "archives"

    if arc_dir.exists():
        shutil.rmtree(arc_dir)
    arc_dir.mkdir(parents=True, exist_ok=True)

    existing_data = load_json()

    new_data = existing_data.copy()
    new_data["COMMON_SETTINGS"] = {
        k: existing_data.get("COMMON_SETTINGS", {}).get(k)
        for k in COMMON_KEYS
    }

    md = []
    md.append("# 📋 Nomenclature (BOM)")
    md.append(f"_Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n")

    # PARAMÈTRES
    c = new_data["COMMON_SETTINGS"]
    md += [
        "## ⚙️ Paramètres d'Impression",
        "| Paramètre | Valeur |",
        "| :--- | :--- |",
        f"| Couches | {c.get('top_solid_layers') or '🔴'} / {c.get('bottom_solid_layers') or '🔴'} |",
        f"| Remplissage | {c.get('fill_density') or '🔴'} / {c.get('fill_pattern') or '🔴'} |",
        "\n---"
    ]

    # 🌳 PARCOURS GLOBAL
    for folder in sorted(root.iterdir()):
        if not folder.is_dir():
            continue
        if folder.name in EXCLUDE:
            continue
        if not contains_stl(folder):
            continue

        walk_tree(folder, root, existing_data, new_data, md, level=0)

        md.append("\n---")

    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    save_json(new_data)

    print("✅ BOM hiérarchique généré (structure respectée à 100%)")


# --- RUN ---
if __name__ == "__main__":
    generate_bom()
