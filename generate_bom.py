import os
import json
from pathlib import Path
import urllib.parse

def generate_bom():
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

    # Extraction des modules (dossiers de niveau 1)
    modules = sorted([d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude])

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ Bill of Materials (BOM) par Module\n\n")

        for module in modules:
            stls = sorted(list(module.rglob("*.stl")))
            if not stls:
                continue

            # Création d'un titre et d'un tableau spécifique pour ce dossier
            f.write(f"## 📦 Module : {module.name.replace('_', ' ')}\n\n")
            f.write("| Structure Hiérarchique | Qualité | Infill | Support | Vue 3D |\n")
            f.write("| :--- | :---: | :---: | :---: | :---: |\n")

            # Parcours hiérarchique à l'intérieur du module
            elements = sorted(list(module.rglob("*")))
            for item in elements:
                if item.is_dir() or item.suffix.lower() == ".stl":
                    rel_path = str(item.relative_to(root_dir))
                    depth = len(item.relative_to(module).parts)
                    
                    # Indentation visuelle
                    indent = "&nbsp;" * 6 * depth + "└── " if depth > 0 else ""
                    icon = "📂" if item.is_dir() else "📄"
                    name = f"**{item.name}**" if item.is_dir() else item.stem

                    # Gestion des paramètres d'impression (seulement pour les fichiers)
                    qlt, inf, sup, view = "-", "-", "-", "-"
                    if item.suffix.lower() == ".stl":
                        settings = print_settings.get(rel_path, {
                            "layer_height": "0.2mm",
                            "infill": "15%",
                            "supports": "Non"
                        })
                        print_settings[rel_path] = settings # Persistence
                        
                        qlt, inf, sup = settings['layer_height'], settings['infill'], settings['supports']
                        url_path = urllib.parse.quote(rel_path)
                        view = f"[👁️]({url_path})"

                    f.write(f"| {indent}{icon} {name} | {qlt} | {inf} | {sup} | {view} |\n")
            
            f.write("\n---\n\n")

    # Sauvegarde du JSON mis à jour
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(print_settings, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    generate_bom()
