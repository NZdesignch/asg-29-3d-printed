import os
import json
from pathlib import Path
import urllib.parse

def vertical(text):
    """Transforme un texte en vertical pour le Markdown."""
    return "<br>".join(list(text))

def generate_bom():
    # --- CONFIGURATION ---
    root_dir = Path(".")
    output_file = "bom.md"
    settings_file = "print_settings.json"
    exclude = {'.git', '.github', '__pycache__', 'venv', '.vscode'}

    # 1. Chargement/Initialisation du dictionnaire
    if Path(settings_file).exists():
        with open(settings_file, "r", encoding="utf-8") as f:
            print_settings = json.load(f)
    else:
        print_settings = {}

    # Paramètres communs (Général)
    common_defaults = {
        "top_solid_layers": None,
        "bottom_solid_layers": None,
        "fill_density": None,
        "fill_pattern": None,
        "infill_anchor": None,
        "infill_anchor_max": None
    }
    
    # On s'assure que la clé COMMON_SETTINGS existe dans le JSON
    if "COMMON_SETTINGS" not in print_settings:
        print_settings["COMMON_SETTINGS"] = common_defaults
    
    common = print_settings["COMMON_SETTINGS"]

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ Bill of Materials (BOM)\n\n")

        # --- SECTION : PARAMÈTRES COMMUNS ---
        f.write("## ⚙️ Paramètres d'Impression Généraux\n")
        f.write("> Ces réglages s'appliquent à l'ensemble des pièces.\n\n")
        f.write(f"- **Couches Solides :** 🔝 {common['top_solid_layers'] or '---'} / ⬇️ {common['bottom_solid_layers'] or '---'}\n")
        f.write(f"- **Remplissage :** {common['fill_density'] or '---'} ({common['fill_pattern'] or '---'})\n")
        f.write(f"- **Ancre d'Infill :** {common['infill_anchor'] or '---'} (Max: {common['infill_anchor_max'] or '---'})\n\n")
        
        f.write("---\n\n")

        # --- PRÉPARATION DES EN-TÊTES VERTICAUX ---
        h_etat = vertical("Statut")
        h_peri = vertical("Périmètres")
        h_vue  = vertical("Vue3D")
        h_down = vertical("Download")

        level1_dirs = [d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude]

        for l1 in level1_dirs:
            level2_dirs = sorted([d for d in l1.iterdir() if d.is_dir()])
            
            for module in level2_dirs:
                stls = sorted(list(module.rglob("*.stl")))
                if not stls: continue

                f.write(f"## 📦 Module : {module.name.replace('_', ' ')}\n")
                f.write(f"Section : `{l1.name}`\n\n")
                
                # Tableau ultra-simplifié
                f.write(f"| Structure | {h_etat} | {h_peri} | {h_vue} | {h_down} |\n")
                f.write("| :--- | :---: | :---: | :---: | :---: |\n")

                for item in sorted(list(module.rglob("*"))):
                    if item.is_dir() or item.suffix.lower() == ".stl":
                        rel_path = str(item.relative_to(root_dir))
                        depth = len(item.relative_to(module).parts)
                        
                        indent = "&nbsp;" * 4 * depth + "/ " if depth > 0 else ""
                        icon = "📂" if item.is_dir() else "📄"
                        
                        status, per, view, dl = ["-"] * 4
                        
                        if item.suffix.lower() == ".stl":
                            # Réglage individuel (Seulement périmètres)
                            if rel_path not in print_settings:
                                print_settings[rel_path] = {"perimeters": None}
                            
                            settings = print_settings[rel_path]
                            
                            # Statut : Vert si périmètre est rempli
                            is_complete = settings.get("perimeters") is not None
                            status = "🟢" if is_complete else "🔴"
                            
                            per = settings.get("perimeters") if is_complete else "---"
                            
                            url_path = urllib.parse.quote(rel_path)
                            view = f"[👁️]({url_path})"
                            dl = f"[💾]({url_path}?raw=true)"

                        name = f"**{item.name}**" if item.is_dir() else item.name
                        f.write(f"| {indent}{icon} {name} | {status} | {per} | {view} | {dl} |\n")
                
                f.write("\n")

    # Sauvegarde JSON
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(print_settings, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    generate_bom()
