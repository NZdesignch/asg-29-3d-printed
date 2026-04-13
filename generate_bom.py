import json
import shutil
import urllib.parse
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
GITHUB_USER = "NZdesignch"
GITHUB_REPO = "asg-29-3d-printed"
BRANCH = "main"

OUTPUT_FILE = "bom.md"
SETTINGS_FILE = "print_settings.json"

EXCLUDE = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives', 'previews'}
COMMON_KEYS = ["top_solid_layers", "bottom_solid_layers", "fill_density", "fill_pattern"]


# --- UTILITAIRES ---
def slugify(text: str) -> str:
    text = text.lower().strip().replace(" ", "-")
    return "".join(c for c in text if c.isalnum() or c in "-_")


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("⚠️ JSON invalide, réinitialisation.")
        return {}


def save_json(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")


def contains_stl(folder: Path) -> bool:
    return any(folder.rglob("*.stl"))


def make_zip(src: Path, dest: Path):
    try:
        shutil.make_archive(str(dest), 'zip', root_dir=src)
        print(f"📦 ZIP créé: {dest}.zip")
    except Exception as e:
        print(f"❌ ZIP échoué: {src} → {dest}.zip | {e}")


def file_size_kb(path: Path) -> float:
    return round(path.stat().st_size / 1024, 1)


# --- 🔥 NOUVELLE LOGIQUE MULTI-NIVEAUX ---
def find_modules(root: Path):
    """Retourne uniquement les dossiers 'modules' contenant des STL (sans doublons)"""
    candidates = []

    for folder in root.rglob("*"):
        if not folder.is_dir():
            continue

        # Exclusions
        if any(part in EXCLUDE for part in folder.parts):
            continue

        if contains_stl(folder):
            candidates.append(folder)

    # ✅ garder seulement les dossiers les plus profonds
    modules = []
    for f in candidates:
        if not any(parent in candidates for parent in f.parents):
            modules.append(f)

    return sorted(modules)


# --- LOGIQUE PRINCIPALE ---
def generate_bom():
    root = Path(".")
    arc_dir = root / "archives"

    # Reset archives
    if arc_dir.exists():
        shutil.rmtree(arc_dir)
    arc_dir.mkdir(parents=True, exist_ok=True)

    raw_base = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}"
    blob_base = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/{BRANCH}"

    existing_data = load_json(Path(SETTINGS_FILE))

    # Ne pas écraser les données existantes
    new_data = existing_data.copy()
    new_data["COMMON_SETTINGS"] = {
        k: existing_data.get("COMMON_SETTINGS", {}).get(k)
        for k in COMMON_KEYS
    }

    # 🔥 modules dynamiques
    modules = find_modules(root)

    sections = []
    for mod in modules:
        parent = mod.parent.name
        sections.append((mod, parent))

    # --- MARKDOWN ---
    md = []
    md.append("# 📋 Nomenclature (BOM)")
    md.append(f"_Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n")

    # --- SOMMAIRE ---
    md.append("## 📌 Sommaire")
    for mod, _ in sections:
        name = mod.name.replace("_", " ").capitalize()
        md.append(f"- [{name}](#{slugify(name)})")

    # --- PARAMÈTRES ---
    c = new_data["COMMON_SETTINGS"]
    md += [
        "\n---",
        "## ⚙️ Paramètres d'Impression",
        "| Paramètre | Valeur |",
        "| :--- | :--- |",
        f"| Couches | {c.get('top_solid_layers') or '🔴'} / {c.get('bottom_solid_layers') or '🔴'} |",
        f"| Remplissage | {c.get('fill_density') or '🔴'} / {c.get('fill_pattern') or '🔴'} |",
        "\n---"
    ]

    # --- MODULES ---
    for mod, parent in sections:
        name = mod.name.replace("_", " ").capitalize()
        zip_name = mod.name.replace(" ", "_")

        make_zip(mod, arc_dir / zip_name)

        zip_url = f"./archives/{urllib.parse.quote(zip_name)}.zip"

        md += [
            f"\n## {name}",
            f"Section : `{parent}` | **[🗜️ ZIP]({zip_url})**\n",
            "| Fichier / Structure | État | Périmètres | Taille | Actions |",
            "| :--- | :---: | :---: | :---: | :--- |"
        ]

        items = sorted(
            mod.rglob("*"),
            key=lambda x: (x.is_file(), x.name.lower())
        )

        for item in items:
            if item.is_file() and item.suffix.lower() != ".stl":
                continue

            rel_path = item.relative_to(root).as_posix()
            depth = len(item.relative_to(mod).parts)
            indent = "&nbsp;" * 6 * (depth - 1) + ("┕ " if depth > 1 else "")

            encoded_path = urllib.parse.quote(rel_path, safe='/')

            if item.is_dir():
                if contains_stl(item):
                    md.append(f"| {indent}📂 **{item.name}** | - | - | - | - |")
                continue

            # STL
            old_val = existing_data.get(rel_path, {}).get("perimeters")

            if rel_path not in new_data:
                new_data[rel_path] = {"perimeters": old_val or None}

            size = file_size_kb(item)

            view_url = f"{blob_base}/{encoded_path}"
            raw_url = f"{raw_base}/{encoded_path}"
            viewer_url = f"https://3dviewer.net/#model={raw_url}"

            md.append(
                f"| {indent}📄 {item.name} | "
                f"{'🟢' if old_val else '🔴'} | "
                f"{old_val or '---'} | "
                f"{size} KB | "
                f"[🔍]({view_url}) [💾]({raw_url}) [🧊]({viewer_url}) |"
            )

        md.append(f"\n[⬆️ Retour au sommaire](#{slugify('sommaire')})\n\n---")

    # --- SAVE ---
    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    save_json(Path(SETTINGS_FILE), new_data)

    print(f"✅ BOM généré avec structure multi-niveaux correcte")


# --- EXECUTION ---
if __name__ == "__main__":
    generate_bom()
