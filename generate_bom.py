import os
import json
import shutil
import subprocess
from pathlib import Path
import urllib.parse

def get_github_repo_info():
    try:
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"]).decode().strip()
        repo_path = remote_url.replace("https://github.com", "").replace(".git", "").replace("git@github.com:", "")
        return f"https://raw.githubusercontent.com{repo_path}/main"
    except Exception:
        return "."

def generate_bom():
    # --- CONFIGURATION ---
    root_dir = Path(".")
    output_file = "bom.md"
    settings_file = "print_settings.json"
    archive_dir = Path("archives")
    exclude = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives'}
    
    archive_dir.mkdir(exist_ok=True)
    base_raw_url = get_github_repo_info()

    # --- 1. LECTURE JSON ---
    existing_data = {}
    if Path(settings_file).exists():
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception as e:
            print(f"❌ Erreur lecture JSON: {e}")
            return 

    # --- 2. PARAMÈTRES COMMUNS ---
    common_keys = ["top_solid_layers", "bottom_solid_layers", "fill_density", "fill_pattern", "infill_anchor", "infill_anchor_max"]
    new_data = {"COMMON_SETTINGS": {}}
    current_common = existing_data.get("COMMON_SETTINGS", {})
    for k in common_keys:
        new_data["COMMON_SETTINGS"][k] = current_common.get(k)
    common = new_data["COMMON_SETTINGS"]

    # --- 3. ANALYSE ---
    level1_dirs = sorted([d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude])
    modules_list = []
    for l1 in level1_dirs:
        l2_dirs = sorted([d for d in l1.iterdir() if d.is_dir()])
        for m in l2_dirs:
            if list(m.rglob("*.stl")):
                modules_list.append((m, l1.name))

    # --- 4. ÉCRITURE DU FICHIER bom.md ---
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ Nomenclature (BOM)\n\n")

        # SOMMAIRE (Modifié : plus de mot "Module")
        f.write("## 📌 Sommaire\n")
        for mod_path, _ in modules_list:
            clean_name = mod_path.name.replace('_', ' ').capitalize()
            anchor = mod_path.name.lower().replace(" ", "-").replace("_", "-")
            f.write(f"- [{clean_name}](#-{anchor})\n")
        f.write("\n---\n\n")

        # PARAMÈTRES GÉNÉRAUX
        f.write("## ⚙️ Paramètres d'Impression Généraux\n\n")
        def check(val): 
            return f"**{val}**" if val and str(val).strip() != "" else "🔴 _À définir_"

        f.write("| Paramètre | Valeur |\n| :--- | :--- |\n")
        f.write(f"| Couches Solides | {check(common['top_solid_layers'])} / {check(common['bottom_solid_layers'])} |\n")
        f.write(f"| Remplissage | {check(common['fill_density'])} / {check(common['fill_pattern'])} |\n")
        f.write(f"| Ancre de remplissage | {check(common['infill_anchor'])} / {check(common['infill_anchor_max'])} |\n\n---\n\n")

        # TABLEAUX (Modifié : plus de mot "Module")
        for module_path, parent_name in modules_list:
            safe_name = module_path.name.replace(" ", "_")
            zip_filename = f"module_{safe_name}" # Le nom du fichier ZIP reste avec "module" pour la structure technique
            shutil.make_archive(str(archive_dir / zip_filename), 'zip', root_dir=module_path)
            
            clean_title = module_path.name.replace('_', ' ').capitalize()
            f.write(f"## 📦 {clean_title}\n")
            f.write(f"Section : `{parent_name}` | **[🗜️ Télécharger ZIP]({base_raw_url}/archives/{urllib.parse.quote(zip_filename)}.zip)**\n\n")
            
            f.write("| Structure | État | Périmètres | Vue 3D | Download |\n| :--- | :---: | :---: | :---: | :---: |\n")

            for item in sorted(list(module_path.rglob("*"))):
                if item.is_dir() or item.suffix.lower() == ".stl":
                    rel_path = str(item.relative_to(root_dir))
                    depth = len(item.relative_to(module_path).parts)
                    indent = "&nbsp;" * 4 * depth + "/ " if depth > 0 else ""
                    
                    if item.suffix.lower() == ".stl":
                        old_perim = existing_data.get(rel_path, {}).get("perimeters")
                        new_data[rel_path] = {"perimeters": old_perim}
                        status = "🟢" if old_perim is not None else "🔴"
                        per = old_perim if old_perim is not None else "---"
                        url_path = urllib.parse.quote(rel_path)
                        f.write(f"| {indent}📄 {item.name} | {status} | {per} | [👁️]({url_path}) | [💾]({base_raw_url}/{url_path}) |\n")
                    else:
                        f.write(f"| {indent}📂 **{item.name}** | - | - | - | - |\n")
            
            f.write("\n[⬆️ Retour au sommaire](#-sommaire)\n\n---\n\n")

    # --- 5. SAUVEGARDE JSON ---
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    generate_bom()
