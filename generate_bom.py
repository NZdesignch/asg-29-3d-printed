import json
import shutil
import subprocess
import urllib.parse
from pathlib import Path

# --- CONFIGURATION ---
OUTPUT_FILE = "bom.md"
SETTINGS_FILE = "print_settings.json"
EXCLUDE = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives', 'previews'}
COMMON_KEYS = [
    "top_solid_layers", "bottom_solid_layers", 
    "fill_density", "fill_pattern", 
    "infill_anchor", "infill_anchor_max"
]

def get_repo_info():
    """Récupère l'URL de base pour le raw (téléchargement) et le blob (viewer)."""
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        repo = url.replace("https://github.com", "").replace("git@github.com:", "").removesuffix(".git")
        raw = f"https://raw.githubusercontent.com{repo}/main"
        blob = f"https://github.com{repo}/blob/main"
        return raw, blob
    except:
        return ".", "."

def check(v):
    return f"**{v}**" if v and str(v).strip() != "" else "🔴 _À définir_"

def generate_bom():
    root = Path(".")
    arc_dir = root / "archives"
    
    if arc_dir.exists(): shutil.rmtree(arc_dir)
    arc_dir.mkdir(exist_ok=True)
    
    raw_url, blob_url = get_repo_info()
    
    existing_data = {}
    if Path(SETTINGS_FILE).exists():
        try: existing_data = json.loads(Path(SETTINGS_FILE).read_text(encoding="utf-8"))
        except: pass

    new_data = {"COMMON_SETTINGS": {k: existing_data.get("COMMON_SETTINGS", {}).get(k) for k in COMMON_KEYS}}

    sections = []
    level1_dirs = sorted([d for d in root.iterdir() if d.is_dir() and d.name not in EXCLUDE])
    for l1 in level1_dirs:
        for m in sorted([d for d in l1.iterdir() if d.is_dir()]):
            if any(m.rglob("*.stl")):
                sections.append((m, l1.name))

    md = ["# 📋 Nomenclature (BOM)\n", "## 📌 Sommaire"]
    for mod_path, _ in sections:
        clean_name = mod_path.name.replace('_', ' ').capitalize()
        anchor = mod_path.name.lower().replace(" ", "-").replace("_", "-")
        md.append(f"- [{clean_name}](#-{anchor})")
    
    c = new_data["COMMON_SETTINGS"]
    md.extend(["\n---\n", "## ⚙️ Paramètres d'Impression\n", "| Paramètre | Valeur |", "| :--- | :--- |",
               f"| Couches | {check(c.get('top_solid_layers'))} / {check(c.get('bottom_solid_layers'))} |",
               f"| Remplissage | {check(c.get('fill_density'))} / {check(c.get('fill_pattern'))} |", "\n---"])

    for mod, parent in sections:
        safe_name = mod.name.replace(" ", "_")
        shutil.make_archive(str(arc_dir / safe_name), 'zip', root_dir=mod)
        zip_url = f"{raw_url}/archives/{urllib.parse.quote(safe_name)}.zip"
        
        md.extend([f"\n## 📦 {mod.name.replace('_', ' ').capitalize()}",
                   f"Section : `{parent}` | **[🗜️ ZIP]({zip_url})**\n",
                   "| Vue 3D | Structure | État | Périmètres | Télécharger |",
                   "| :---: | :--- | :---: | :---: | :---: |"])

    # --- PARTIE MODIFIÉE POUR L'OUVERTURE EN NOUVEL ONGLET ---
        for item in sorted(mod.rglob("*")):
            if not (item.is_dir() or item.suffix.lower() == ".stl"): continue
            
            rel_path = item.relative_to(root)
            depth = len(item.relative_to(mod).parts)
            indent = "&nbsp;" * 4 * depth + "/ " if depth > 0 else ""
            
            if item.suffix.lower() == ".stl":
                u_path = urllib.parse.quote(str(rel_path.as_posix()))
                
                # Utilisation de la balise <a> pour forcer le target="_blank"
                view_link = f'<a href="{blob_url}/{u_path}" target="_blank">👁️ Voir</a>'
                download_link = f'[💾]({raw_url}/{u_path})'
                
                old_val = existing_data.get(str(rel_path), {}).get("perimeters")
                new_data[str(rel_path)] = {"perimeters": old_val}
                
                md.append(f"| {view_link} | {indent}📄 {item.name} | {'🟢' if old_val else '🔴'} | {old_val or '---'} | {download_link} |")
            else:
                md.append(f"| | {indent}📂 **{item.name}** | - | - | - |")
        
        md.append("\n[⬆️ Sommaire](#-sommaire)\n\n---")

    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    Path(SETTINGS_FILE).write_text(json.dumps(new_data, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"✅ BOM généré : Liens 3D configurés pour nouvel onglet.")

if __name__ == "__main__":
    generate_bom()
