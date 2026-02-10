import os
import json
import shutil
import subprocess
from pathlib import Path
import urllib.parse

def get_github_repo_info():
    """Récupère l'URL raw de GitHub."""
    try:
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"]).decode().strip()
        repo_path = remote_url.replace("https://github.com", "").replace(".git", "").replace("git@github.com:", "")
        return f"https://raw.githubusercontent.com{repo_path}/main"
    except Exception:
        return "."

def generate_bom():
    root_dir = Path(".")
    output_file = "bom.md"
    settings_file = "print_settings.json"
    archive_dir = Path("archives")
    exclude = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives'}
    
    archive_dir.mkdir(exist_ok=True)
    base_raw_url = get_github_repo_info()

    if Path(settings_file).exists():
        with open(settings_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    common_keys = ["top_solid_layers", "bottom_solid_layers", "fill_density", "fill_pattern", "infill_anchor", "infill_anchor_max"]
    if "COMMON_SETTINGS" not in data:
        data["COMMON_SETTINGS"] = {k: None for k in common_keys}
    
    common = data["COMMON_SETTINGS"]
    new_print_settings = {"COMMON_SETTINGS": common}

    level1_dirs = sorted([d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude])
    modules_list = []
    for l1 in level1_dirs:
        l2_dirs = sorted([d for d in l1.iterdir() if d.is_dir()])
        for m in l2_dirs:
            if list(m.rglob("*.stl")):
                modules_list.append((m, l1.name))

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ Nomenclature (BOM)\n\n")

        f.write("## 📌 Sommaire\n")
        for mod_path, _ in modules_list:
            anchor = mod_path.name.lower().replace(" ", "-").replace("_", "-")
            f.write(f"- [Module : {mod_path.name.replace('_', ' ')}](#-module--{anchor})\n")
        f.write("\n---\n\n")

        f.write("## ⚙️ Paramètres d'Impression Généraux\n\n")
        def check(val): return val if val is not None else "🔴 _À définir_"
        f.write("| Paramètre | Valeur |\n| :--- | :--- |\n")
        f.write(f"| Couches Solides (Dessus / Dessous) | {check(common['top_solid_layers'])} / {check(common['bottom_solid_layers'])} |\n")
        f.write(f"| Remplissage (Densité / Motif) | {check(common['fill_density'])} / {check(common['fill_pattern'])} |\n")
        f.write(f"| Ancre de remplissage (Valeur / Max) | {check(common['infill_anchor'])} / {check(common['infill_anchor_max'])} |\n\n")
        f.write("---\n\n")

        for module_path, parent_name in modules_list:
            # --- CORRECTION DES ESPACES DANS LES ZIP ---
            # On remplace les espaces par des underscores pour le nom du fichier réel
            safe_name = module_path.name.replace(" ", "_")
            zip_filename = f"module_{safe_name}"
            
            # Création physique du ZIP
            shutil.make_archive(str(archive_dir / zip_filename), 'zip', root_dir=module_path)
            
            # Encodage URL du nom de fichier pour le lien Markdown
            url_zip_name = urllib.parse.quote(f"{zip_filename}.zip")
            zip_url = f"{base_raw_url}/archives/{url_zip_name}"

            f.write(f"## 📦 Module : {module_path.name.replace('_', ' ')}\n")
            f.write(f"Section : `{parent_name}` | **[🗜️ Télécharger ZIP]({zip_url})**\n\n")
            
            f.write("| Structure | État | Périmètres | Vue 3D | Download |\n| :--- | :---: | :---: | :---: | :---: |\n")

            for item in sorted(list(module_path.rglob("*"))):
                if item.is_dir() or item.suffix.lower() == ".stl":
                    rel_path = str(item.relative_to(root_dir))
                    depth = len(item.relative_to(module_path).parts)
                    indent = "&nbsp;" * 4 * depth + "/ " if depth > 0 else ""
                    status, per, view, dl = ["-"] * 4
                    
                    if item.suffix.lower() == ".stl":
                        old_val = data.get(rel_path, {}).get("perimeters", None)
                        new_print_settings[rel_path] = {"perimeters": old_val}
                        status = "🟢" if old_val is not None else "🔴"
                        per = old_val if old_val is not None else "---"
                        url_path = urllib.parse.quote(rel_path)
                        view = f"[👁️]({url_path})"
                        dl = f"[💾]({base_raw_url}/{url_path})"

                    icon = "📂" if item.is_dir() else "📄"
                    name = f"**{item.name}**" if item.is_dir() else item.name
                    f.write(f"| {indent}{icon} {name} | {status} | {per} | {view} | {dl} |\n")
                
            f.write("\n[⬆️ Retour au sommaire](#-sommaire)\n\n---\n\n")

    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(new_print_settings, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    generate_bom()
