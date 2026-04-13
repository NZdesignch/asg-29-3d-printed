import json
import shutil
import urllib.parse
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
GITHUB_USER = "VOTRE_NOM_UTILISATEUR"
GITHUB_REPO = "VOTRE_NOM_DE_DEPOT"
BRANCH = "main"

OUTPUT_FILE = "bom.md"
SETTINGS_FILE = "print_settings.json"

EXCLUDE = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives', 'previews'}
COMMON_KEYS = ["top_solid_layers", "bottom_solid_layers", "fill_density", "fill_pattern"]


# --- UTILITAIRES ---
def slugify(text: str) -> str:
    slug = text.lower().strip().replace(" ", "-")
    return "".join(c for c in slug if c.isalnum() or c in "-_")


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
    return any(f.suffix.lower() == ".stl" for f in folder.rglob("*") if f.is_file())


def make_zip(src: Path, dest: Path):
    try:
        shutil.make_archive(str(dest), 'zip', root_dir=src)
    except Exception as e:
        print(f"❌ Erreur ZIP {src}: {e}")


# --- LOGIQUE PRINCIPALE ---
def generate_bom():
    root = Path(".")
    arc_dir = root / "archives"

    # Reset dossier archives
    if arc_dir.exists():
        shutil.rmtree(arc_dir)
    arc_dir.mkdir(parents=True, exist_ok=True)

    # URLs GitHub (FIX IMPORTANT ici ✅)
    raw_base = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}"
    blob_base = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/blob/{BRANCH}"

    existing_data = load_json(Path(SETTINGS_FILE))

    new_data = {
        "COMMON_SETTINGS": {
            k: existing_data.get("COMMON_SETTINGS", {}).get(k)
            for k in COMMON_KEYS
        }
    }

    sections = []

    # Scan dossiers (niveau 1 + 2)
    for l1 in sorted(p for p in root.iterdir() if p.is_dir() and p.name not in EXCLUDE):
        for l2 in sorted(p for p in l1.iterdir() if p.is_dir()):
            if contains_stl(l2):
                sections.append((l2, l1.name))

    # --- MARKDOWN ---
    md = []
    md.append("# 📋 Nomenclature (BOM)")
    md.append(f"_Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n")

    # --- SOMMAIRE ---
    md.append("## 📌 Sommaire")
    for mod, _ in sections:
        name = mod.name.replace("_", " ").capitalize()
        md.append(f"- [{name}](#{slugify('📦 ' + name)})")

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

        zip_url = f"{raw_base}/archives/{urllib.parse.quote(zip_name)}.zip"

        md += [
            f"\n## 📦 {name}",
            f"Section : `{parent}` | **[🗜️ ZIP]({zip_url})**\n",
            "| Fichier / Structure | État | Périmètres | Actions |",
            "| :--- | :---: | :---: | :---: |"
        ]

        for item in sorted(mod.rglob("*")):
            if item.is_file() and item.suffix.lower() != ".stl":
                continue

            rel_path = item.relative_to(root).as_posix()
            depth = len(item.relative_to(mod).parts)
            indent = "&nbsp;" * 6 * (depth - 1) + ("┕ " if depth > 1 else "")

            encoded_path = urllib.parse.quote(rel_path, safe='/')

            if item.is_dir():
                if contains_stl(item):
                    md.append(f"| {indent}📂 **{item.name}** | - | - | - |")
                continue

            # Fichier STL
            old_val = existing_data.get(rel_path, {}).get("perimeters")
            new_data[rel_path] = {"perimeters": old_val}

            view_url = f"{blob_base}/{encoded_path}"
            raw_url = f"{raw_base}/{encoded_path}"

            md.append(
                f"| {indent}📄 {item.name} | {'🟢' if old_val else '🔴'} | "
                f"{old_val or '---'} | [🔍 Voir]({view_url}) / [💾 RAW]({raw_url}) |"
            )

        md.append(f"\n[⬆️ Retour au sommaire](#{slugify('📌 Sommaire')})\n\n---")

    # --- SAUVEGARDE ---
    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    save_json(Path(SETTINGS_FILE), new_data)

    print(f"✅ BOM généré pour {GITHUB_USER}/{GITHUB_REPO}")


# --- EXECUTION ---
if __name__ == "__main__":
    generate_bom()
