import os
from pathlib import Path
import urllib.parse

def generate_bom():
    root_dir = Path(".")
    output_file = "bom.md"
    exclude = {'.git', '.github', '__pycache__', 'venv', '.vscode'}

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ Bill of Materials (BOM) - Inventaire par Modules\n\n")

        # Extraction des dossiers de niveau 1 (les modules principaux)
        modules = sorted([d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude])

        for module in modules:
            # On vérifie si le module contient des fichiers STL
            all_stls = list(module.rglob("*.stl"))
            if not all_stls:
                continue

            # --- TITRE DU TABLEAU (Nom du dossier de niveau 1) ---
            f.write(f"## 📦 Module : {module.name.replace('_', ' ')}\n\n")
            
            f.write("| Structure Hiérarchique | Type | Visualisation | Chemin |\n")
            f.write("| :--- | :---: | :---: | :--- |\n")

            # Parcours de tous les éléments à l'intérieur de ce module spécifique
            # On utilise rglob("*") pour récupérer dossiers ET fichiers
            elements = sorted(list(module.rglob("*")))
            
            # On ajoute le dossier racine du module lui-même en haut du tableau
            f.write(f"| 📂 **{module.name}** | Dossier | | `{module.name}` |\n")

            for item in elements:
                # Filtrage : seulement dossiers ou fichiers STL
                if item.is_dir() or item.suffix.lower() == ".stl":
                    # Calcul de la profondeur relative au module (pour l'indentation)
                    depth = len(item.relative_to(module).parts)
                    
                    # Style visuel pour la hiérarchie
                    indent = "&nbsp;" * 6 * depth + "└── "
                    icon = "📂" if item.is_dir() else "📄"
                    
                    # Lien vers l'aperçu 3D de GitHub
                    view_link = ""
                    if item.suffix.lower() == ".stl":
                        url_path = urllib.parse.quote(str(item.relative_to(root_dir)))
                        view_link = f"[👁️ Voir]({url_path})"
                    
                    # Nom d'affichage
                    name = f"**{item.name}**" if item.is_dir() else item.name
                    rel_path = f"`{item.relative_to(root_dir)}`"

                    f.write(f"| {indent}{icon} {name} | {'Dossier' if item.is_dir() else 'STL'} | {view_link} | {rel_path} |\n")
            
            f.write("\n---\n\n") # Ligne de séparation entre les tableaux

    print(f"✅ BOM sectorisé généré dans {output_file}")

if __name__ == "__main__":
    generate_bom()
