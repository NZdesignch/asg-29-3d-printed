import os
import json
from pathlib import Path
import urllib.parse

def generate_bom():
    # Configuration
    root_dir = Path(".")
    output_file = "bom.md"
    settings_file = "print_settings.json"
    exclude = {'.git', '.github', '__pycache__', 'venv', '.vscode'}

    # Chargement des réglages existants
    if Path(settings_file).exists():
        with open(settings_file, "r", encoding="utf-8") as f:
            print_settings = json.load(f)
    else:
        print_settings = {}

    # 1. Identifier les dossiers de 1er niveau (ex: MTL)
    level1_dirs = [d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude]

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ BOM Sectorisé (Niveau 2)\n\n")

        for l1 in level1_dirs:
            # 2. Identifier les dossiers de 2ème niveau (ex: Aile Gauche, Fuselage)
            level2_dirs = sorted([d for d in l1.iterdir() if d.is_dir()])
            
            for module in level2_dirs:
                stls = sorted(list(module.rglob("*.stl")))
                if not stls: continue

                # Création d'un tableau pour chaque dossier de niveau 2
                f.write(f"## 📦 Module : {module.name.replace('_', ' ')}\n")
                f.write(f"Parent : `{l1.name}`\n\n")
                
                f.write("| Structure | Qualité | Infill | Support | Vue 3D |\n")
                f.write("| :--- | :---: | :---: | :---: | :---: |\n")

                # Parcours interne au module
                for item in sorted(list(module.rglob("*"))):
                    if item.is_dir() or item.suffix.lower() == ".stl":
                        rel_path = str(item.relative_to(root_dir))
                        depth = len(item.relative_to(module).parts)
                        
                        indent = "&nbsp;" * 6 * depth + "└── " if depth > 0 else ""
                        icon = "📂" if item.is_dir() else "📄"
                        
                        qlt, inf, sup, view = "-", "-", "-", "-"
                        if item.suffix.lower() == ".stl":
                            settings = print_settings.get(rel_path, {"layer_height": "0.2mm", "infill": "15%", "supports": "Non"})
                            print_settings[rel_path] = settings
                            qlt, inf, sup = settings['layer_height'], settings['infill'], settings['supports']
                            view = f"[👁️]({urllib.parse.quote(rel_path)})"

                        f.write(f"| {indent}{icon} {item.name} | {qlt} | {inf} | {sup} | {view} |\n")
                
                f.write("\n---\n\n")

    # Sauvegarde JSON
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(print_settings, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    generate_bom()
