import json
import shutil
import subprocess
import urllib.parse
from pathlib import Path

# --- CONFIGURATION ---
OUTPUT_FILE = "bom.md"
SETTINGS_FILE = "print_settings.json"
EXCLUDE = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives', 'previews'}
COMMON_KEYS = ["top_solid_layers", "bottom_solid_layers", "fill_density", "fill_pattern"]

def slugify(text):
    """Formatage d'ancre GitHub : minuscule, espaces -> tirets, retire ponctuation."""
    slug = text.lower().replace(" ", "-")
    return "".join(c for c in slug if c.isalnum() or c in "-_")

def get_repo_info():
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], 
                                       text=True, stderr=subprocess.DEVNULL).strip()
        repo = url.replace("https://github.com", "").replace("git@github.com:", "").removesuffix(".git").strip("/")
        return f"https://raw.githubusercontent.com{repo}/main", f"https://github.com{repo}/blob/main"
    except:
        return ".", "."

def check_val(v):
    return f"**{v}**" if v and str(v).strip() else "🔴 _À définir_"

def generate_bom():
    root = Path(".")
    arc_dir = root / "archives"
    if arc_dir.exists(): shutil.rmtree(arc_dir)
    arc_dir.mkdir(parents=True, exist_ok=True)

    raw_base, blob_base = get_repo_info()
    existing_data = {}
    if Path(SETTINGS_FILE).exists():
        try: existing_data = json.loads(Path(SETTINGS_FILE).read_text(encoding="utf-8"))
        except: pass

    new_data = {"COMMON_SETTINGS": {k: existing_data.get("COMMON_SETTINGS", {}).get(k) for k in COMMON_KEYS}}

    sections = []
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
           f"| Couches | {check_val(c.get('top_solid_layers'))} / {check_val(c.get('bottom_solid_layers'))} |",
           f"| Remplissage | {check_val(c.get('fill_density'))} / {check_val(c.get('fill_pattern'))} |", "\n---"]

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

        for item in sorted(mod.rglob("*")):
            if item.is_file() and item.suffix.lower() != ".stl": continue
            
            depth = len(item.relative_to(mod).parts)
            indent = "&nbsp;" * 6 * (depth - 1) + ("┕ " if depth > 1 else "")
            rel_path_str = item.relative_to(root).as_posix()
            u_path = urllib.parse.quote(rel_path_str, safe='/')

            if item.is_dir():
                if any(item.rglob("*.stl")):
                    md.append(f"| {indent}📂 **{item.name}** | - | - | - |")
            else:
                old_val = existing_data.get(rel_path_str, {}).get("perimeters")
                new_data[rel_path_str] = {"perimeters": old_val}
                md.append(f"| {indent}📄 {item.name} | {'🟢' if old_val else '🔴'} | {old_val or '---'} | [🔍 Voir]({blob_base}/{u_path}) / [💾 RAW]({raw_base}/{u_path}) |")

        md.append(f"\n[⬆️ Retour au sommaire](#{slugify('📌 Sommaire')})\n\n---")

    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    Path(SETTINGS_FILE).write_text(json.dumps(new_data, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"✅ BOM généré avec ancres corrigées.")

if __name__ == "__main__":
    generate_bom()
