import json
import shutil
import subprocess
import urllib.parse
from pathlib import Path

# --- CONFIGURATION MANUELLE (Plus fiable) ---
# Remplacez par vos vraies infos GitHub
GITHUB_USER = "NZdesignch"
GITHUB_REPO = "asg-29-3d-printed"
BRANCH = "main"  # ou "master"

OUTPUT_FILE = "bom.md"
SETTINGS_FILE = "print_settings.json"
EXCLUDE = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives', 'previews'}
COMMON_KEYS = ["top_solid_layers", "bottom_solid_layers", "fill_density", "fill_pattern"]

def slugify(text):
    """Formatage d'ancre GitHub : minuscule, espaces -> tirets, retire ponctuation."""
    # GitHub garde les emojis dans l'ID de l'ancre
    slug = text.lower().strip().replace(" ", "-")
    return "".join(c for c in slug if c.isalnum() or c in "-_")

def generate_bom():
    root = Path(".")
    arc_dir = root / "archives"
    if arc_dir.exists(): shutil.rmtree(arc_dir)
    arc_dir.mkdir(parents=True, exist_ok=True)

    # URLs GitHub construites proprement
    raw_base = f"https://raw.githubusercontent.com{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}"
    blob_base = f"https://github.com{GITHUB_USER}/{GITHUB_REPO}/blob/{BRANCH}"

    existing_data = {}
    if Path(SETTINGS_FILE).exists():
        try: existing_data = json.loads(Path(SETTINGS_FILE).read_text(encoding="utf-8"))
        except: pass

    new_data = {"COMMON_SETTINGS": {k: existing_data.get("COMMON_SETTINGS", {}).get(k) for k in COMMON_KEYS}}

    sections = []
    # On scanne les dossiers niveau 1 puis niveau 2
    for l1 in sorted(d for d in root.iterdir() if d.is_dir() and d.name not in EXCLUDE):
        for m in sorted(d for d in l1.iterdir() if d.is_dir()):
            if any(m.rglob("*.stl")):
                sections.append((m, l1.name))

    # --- SOMMAIRE ---
    md = ["# 📋 Nomenclature (BOM)\n", "## 📌 Sommaire"]
    for m, _ in sections:
        display_name = m.name.replace('_', ' ').capitalize()
        anchor = slugify(f"📦 {display_name}")
        md.append(f"- [{display_name}](#{anchor})")

    # --- PARAMÈTRES ---
    c = new_data["COMMON_SETTINGS"]
    md += ["\n---\n", "## ⚙️ Paramètres d'Impression\n", "| Paramètre | Valeur |", "| :--- | :--- |",
           f"| Couches | {c.get('top_solid_layers') or '🔴'} / {c.get('bottom_solid_layers') or '🔴'} |",
           f"| Remplissage | {c.get('fill_density') or '🔴'} / {c.get('fill_pattern') or '🔴'} |", "\n---"]

    # --- MODULES ---
    for mod, parent in sections:
        display_name = mod.name.replace('_', ' ').capitalize()
        safe_zip_name = mod.name.replace(" ", "_")
        shutil.make_archive(str(arc_dir / safe_zip_name), 'zip', root_dir=mod)
        
        zip_url = f"{raw_base}/archives/{urllib.parse.quote(safe_zip_name)}.zip"

        md += [f"\n## 📦 {display_name}",
               f"Section : `{parent}` | **[🗜️ ZIP]({zip_url})**\n",
               "| Fichier / Structure | État | Périmètres | Actions |",
               "| :--- | :---: | :---: | :---: |"]

        # Parcours hiérarchique
        for item in sorted(mod.rglob("*")):
            if item.is_file() and item.suffix.lower() != ".stl": continue
            
            rel_path_str = item.relative_to(root).as_posix()
            depth = len(item.relative_to(mod).parts)
            indent = "&nbsp;" * 6 * (depth - 1) + ("┕ " if depth > 1 else "")
            
            # Encodage du chemin pour les liens GitHub (safe='/')
            u_path = urllib.parse.quote(rel_path_str, safe='/')

            if item.is_dir():
                if any(item.rglob("*.stl")):
                    md.append(f"| {indent}📂 **{item.name}** | - | - | - |")
            else:
                old_val = existing_data.get(rel_path_str, {}).get("perimeters")
                new_data[rel_path_str] = {"perimeters": old_val}
                
                view_url = f"{blob_base}/{u_path}"
                raw_url = f"{raw_base}/{u_path}"
                
                md.append(f"| {indent}📄 {item.name} | {'🟢' if old_val else '🔴'} | {old_val or '---'} | [🔍 Voir]({view_url}) / [💾 RAW]({raw_url}) |")

        md.append(f"\n[⬆️ Retour au sommaire](#{slugify('📌 Sommaire')})\n\n---")

    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    Path(SETTINGS_FILE).write_text(json.dumps(new_data, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"✅ BOM généré pour {GITHUB_USER}/{GITHUB_REPO}")

if __name__ == "__main__":
    generate_bom()
