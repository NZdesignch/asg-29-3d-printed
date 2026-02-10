import os
import json
from pathlib import Path
import urllib.parse

def generate_bom():
    # --- CONFIGURATION ---
    root_dir = Path(".")
    output_file = "bom.md"
    settings_file = "print_settings.json"
    exclude = {'.git', '.github', '__pycache__', 'venv', '.vscode'}

    # 1. Chargement et Nettoyage du JSON
    if Path(settings_file).exists():
        with open(settings_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    # Paramètres partagés
    common_keys = [
        "top_solid_layers", "bottom_solid_layers", 
        "fill_density", "fill_pattern", 
        "infill_anchor", "infill_anchor_max"
    ]
    
    if "COMMON_SETTINGS" not in data:
        data["COMMON_SETTINGS"] = {k: None for k in common_keys}
    
    common = data["COMMON_SETTINGS"]
    new_print_settings = {"COMMON_SETTINGS": common}

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ Bill of Materials (BOM)\n\n")

        # --- TABLEAU DES PARAMÈTRES COMMUNS (Texte pur) ---
        f.write("## ⚙️ Paramètres d'Impression Généraux\n\n")
        
        def check(val): return val if val is not None else "🔴 _À définir_"

        f.write("| Paramètre | Valeur |\n")
        f.write("| :--- | :--- |\n")
        # Suppression des icônes 🔝 et ⬇️ ici
        f.write(f"| Couches Solides (Top / Bot) | {check(common['top_solid_layers'])} / {check(common['bottom_solid_layers'])} |\n")
        f.write(f"| Remplissage (Densité / Motif) | {check(common['fill_density'])} / {check(common['fill_pattern'])} |\n")
        f.write(f"| Ancre d'Infill (Valeur / Max) | {check(common['infill_anchor'])} / {check(common['infill_anchor_max'])} |\n\n")
        
        f.write("---\n\n")

        # --- GÉNÉRATION DES TABLEAUX PAR MODULE ---
        level1_dirs = [d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude]

        for l1 in level1_dirs:
            level2_dirs = sorted([d for d in l1.iterdir() if d.is_dir()])
            
            for module in level2_dirs:
                stls = sorted(list(module.rglob("*.stl")))
                if not stls: continue

                f.write(f"## 📦 Module : {module.name.replace('_', ' ')}\n")
                f.write(f"Section : `{l1.name}`\n\n")
                
                f.write("| Structure | État | Périmètres | Vue 3D | Download |\n")
                f.write("| :--- | :---: | :---: | :---: | :---: |\n")

                for item in sorted(list(module.rglob("*"))):
                    if item.is_dir() or item.suffix.lower() == ".stl":
                        rel_path = str(item.relative_to(root_dir))
                        depth = len(item.relative_to(module).parts)
                        indent = "&nbsp;" * 4 * depth + "/ " if depth > 0 else ""
                        
                        status, per, view, dl = ["-"] * 4
                        
                        if item.suffix.lower() == ".stl":
                            old_val = data.get(rel_path, {}).get("perimeters", None)
                            new_print_settings[rel_path] = {"perimeters": old_val}
                            
                            status = "🟢" if old_val is not None else "🔴"
                            per = old_val if old_val is not None else "---"
                            
                            url_path = urllib.parse.quote(rel_path)
                            view = f"[👁️]({url_path})"
                            dl = f"[💾]({url_path}?raw=true)"

                        icon = "📂" if item.is_dir() else "📄"
                        name = f"**{item.name}**" if item.is_dir() else item.name
                        f.write(f"| {indent}{icon} {name} | {status} | {per} | {view} | {dl} |\n")
                
                f.write("\n---\n\n")

    # Sauvegarde du JSON
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(new_print_settings, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    generate_bom()
