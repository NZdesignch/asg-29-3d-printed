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

    # Chargement des réglages d'impression (JSON)
    if Path(settings_file).exists():
        with open(settings_file, "r", encoding="utf-8") as f:
            print_settings = json.load(f)
    else:
        print_settings = {}

    # Extraction du 1er niveau (ex: MTL)
    level1_dirs = [d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude]

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ BOM & Centre de Téléchargement STL\n\n")

        for l1 in level1_dirs:
            # Extraction du 2ème niveau (ex: Aile_Gauche, Fuselage)
            level2_dirs = sorted([d for d in l1.iterdir() if d.is_dir()])
            
            for module in level2_dirs:
                stls = sorted(list(module.rglob("*.stl")))
                if not stls: continue

                # Titre du module
                f.write(f"## 📦 Module : {module.name.replace('_', ' ')}\n")
                f.write(f"Section : `{l1.name}`\n\n")
                
                # Entête du tableau avec les colonnes de visualisation et téléchargement
                f.write("| Structure | Qualité | Infill | Support | Vue 3D | Download |\n")
                f.write("| :--- | :---: | :---: | :---: | :---: | :---: |\n")

                for item in sorted(list(module.rglob("*"))):
                    if item.is_dir() or item.suffix.lower() == ".stl":
                        rel_path = str(item.relative_to(root_dir))
                        depth = len(item.relative_to(module).parts)
                        
                        # Style de l'arborescence
                        indent = "&nbsp;" * 6 * depth + "└── " if depth > 0 else ""
                        icon = "📂" if item.is_dir() else "📄"
                        
                        qlt, inf, sup, view, dl = "-", "-", "-", "-", "-"
                        
                        if item.suffix.lower() == ".stl":
                            # Gestion des paramètres via JSON
                            settings = print_settings.get(rel_path, {
                                "layer_height": "0.2mm", 
                                "infill": "15%", 
                                "supports": "Non"
                            })
                            print_settings[rel_path] = settings
                            
                            qlt, inf, sup = settings['layer_height'], settings['infill'], settings['supports']
                            
                            # Encodage de l'URL pour GitHub
                            url_path = urllib.parse.quote(rel_path)
                            
                            # Colonne Vue 3D (Visionneuse interactive)
                            view = f"[👁️]({url_path})"
                            
                            # Colonne Download (Lien direct vers le fichier brut)
                            # On utilise le chemin relatif direct, GitHub gère le téléchargement
                            dl = f"[💾]({url_path}?raw=true)"

                        name = f"**{item.name}**" if item.is_dir() else item.name
                        f.write(f"| {indent}{icon} {name} | {qlt} | {inf} | {sup} | {view} | {dl} |\n")
                
                f.write("\n---\n\n")

    # Mise à jour du fichier JSON
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(print_settings, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    generate_bom()
