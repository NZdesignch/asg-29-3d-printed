import os
from pathlib import Path
import urllib.parse

def generate_bom():
    root_dir = Path(".")
    output_file = "bom.md"
    # Dossiers à ignorer
    exclude = {'.git', '.github', '__pycache__', 'venv', '.vscode'}

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ Bill of Materials (BOM) par Composants\n\n")
        f.write("> Ce fichier recense tous les fichiers STL classés par dossiers principaux.\n\n")

        # Récupération des dossiers de premier niveau (ex: Aile Gauche, Fuselage...)
        top_folders = sorted([d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude])

        if not top_folders:
            f.write("_Aucun dossier de composants trouvé._\n")
            return

        for folder in top_folders:
            # On vérifie s'il y a des fichiers STL dans ce dossier ou ses sous-dossiers
            all_stls = list(folder.rglob("*.stl"))
            if not all_stls:
                continue

            # Titre pour le dossier de premier niveau
            f.write(f"## 📦 Section : {folder.name.replace('_', ' ')}\n\n")
            
            # Début du tableau pour ce dossier spécifique
            f.write("| Structure Hiérarchique | Type | Visualisation | Chemin relatif |\n")
            f.write("| :--- | :---: | :---: | :--- |\n")

            # Parcours de tous les éléments à l'intérieur (fichiers et sous-dossiers)
            # On trie pour garder une cohérence visuelle
            sub_elements = sorted(list(folder.rglob("*")))
            
            for item in sub_elements:
                # On ne traite que les dossiers ou les fichiers STL
                if item.is_dir() or item.suffix.lower() == ".stl":
                    # Calcul de la profondeur relative au dossier parent (folder)
                    depth = len(item.relative_to(folder).parts)
                    
                    # Indentation visuelle
                    # Niveau 0 (directement dans le dossier) = pas d'indentation
                    # Niveau 1+ = indentation avec connecteur
                    if depth == 1:
                        indent = ""
                        display_name = f"**{item.name}**"
                    else:
                        indent = "&nbsp;" * 6 * (depth - 1) + "└── "
                        display_name = item.name

                    # Icônes
                    icon = "📂" if item.is_dir() else "📄"
                    
                    # Lien de visualisation 3D (GitHub)
                    link = ""
                    if item.suffix.lower() == ".stl":
                        url_path = urllib.parse.quote(str(item.relative_to(root_dir)))
                        link = f"[👁️ Aperçu]({url_path})"
                    
                    rel_path = f"`{item.relative_to(root_dir)}`"
                    
                    f.write(f"| {indent}{icon} {display_name} | {'Dossier' if item.is_dir() else 'STL'} | {link} | {rel_path} |\n")
            
            f.write("\n---\n\n") # Séparateur entre les tableaux

    print(f"✅ BOM généré avec succès dans {output_file}")

if __name__ == "__main__":
    generate_bom()
