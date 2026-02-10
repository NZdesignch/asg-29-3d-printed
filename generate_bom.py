import os
from pathlib import Path
import urllib.parse

def generate_bom():
    root_dir = Path(".")
    output_file = "bom.md"
    exclude = {'.git', '.github', '__pycache__', '.vscode'}

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ Bill of Materials (BOM) - Modèles STL\n\n")
        f.write(f"Généré automatiquement le : {Path(output_file).stat().st_mtime}\n\n")

        # --- SECTION 1 : Tableaux par dossier (Niveau 1) ---
        top_folders = sorted([d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude])
        
        for folder in top_folders:
            stls = sorted(list(folder.rglob("*.stl")))
            if stls:
                f.write(f"## 📁 Catégorie : {folder.name}\n\n")
                f.write("| Pièce | Qté | Aperçu | Chemin |\n")
                f.write("| :--- | :---: | :---: | :--- |\n")
                for stl in stls:
                    rel_path = stl.relative_to(root_dir)
                    # Encodage de l'URL pour les espaces et caractères spéciaux
                    url_path = urllib.parse.quote(str(rel_path))
                    # On laisse la Qté à 1 par défaut pour le BOM
                    f.write(f"| {stl.stem} | 1 | [🔗 Voir]({url_path}) | `{rel_path}` |\n")
                f.write("\n")

        # --- SECTION 2 : Récapitulatif Multi-niveaux ---
        f.write("## 🗂️ Liste Globale de Fabrication\n\n")
        f.write("| Sous-dossier | Nom du fichier | Lien direct |\n")
        f.write("| :--- | :--- | :--- |\n")
        
        all_stls = sorted(list(root_dir.rglob("*.stl")))
        for stl in all_stls:
            parent_name = stl.parent.name if stl.parent != root_dir else "Racine"
            url_path = urllib.parse.quote(str(stl.relative_to(root_dir)))
            f.write(f"| `{parent_name}` | {stl.name} | [Ouvrir]({url_path}) |\n")

    print(f"✅ Fichier '{output_file}' généré avec succès.")

if __name__ == "__main__":
    generate_bom()
