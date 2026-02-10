import os
from pathlib import Path
import urllib.parse

def generate_bom():
    root_dir = Path(".")
    output_file = "bom.md"
    exclude = {'.git', '.github', '__pycache__', 'venv'}

    def get_tree_structure(path, root):
        parts = list(path.relative_to(root).parts)
        depth = len(parts) - 1
        if depth == 0:
            return f"**{path.name}**"
        
        # Création de l'indentation visuelle avec connecteurs
        indent = "&nbsp;" * 6 * (depth - 1)
        connector = "└── "
        return f"{indent}{connector}{path.name}"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ Bill of Materials (BOM) Hiérarchique\n\n")

        # --- SECTION 1 : Tableaux par dossier Racine ---
        top_folders = sorted([d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude])
        
        for top_folder in top_folders:
            f.write(f"## 📂 Dossier : {top_folder.name}\n\n")
            f.write("| Structure Hiérarchique | Type | Vue 3D | Chemin |\n")
            f.write("| :--- | :---: | :---: | :--- |\n")
            
            # Récupérer TOUS les éléments (dossiers et fichiers STL) de ce dossier
            all_elements = sorted(list(top_folder.rglob("*")))
            
            for item in all_elements:
                if any(ex in item.parts for ex in exclude): continue
                if item.is_dir() or item.suffix.lower() == ".stl":
                    
                    # Formater le nom avec icône et indentation
                    display_name = get_tree_structure(item, top_folder)
                    icon = "📂" if item.is_dir() else "📄"
                    
                    # Lien 3D seulement pour les fichiers
                    link = ""
                    if item.suffix.lower() == ".stl":
                        url_path = urllib.parse.quote(str(item.relative_to(root_dir)))
                        link = f"[👁️ Voir]({url_path})"
                    
                    rel_path = f"`{item.relative_to(root_dir)}`"
                    
                    f.write(f"| {icon} {display_name} | {'Dossier' if item.is_dir() else 'STL'} | {link} | {rel_path} |\n")
            f.write("\n")

if __name__ == "__main__":
    generate_bom()
