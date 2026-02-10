import os
from pathlib import Path

def generate_stl_markdown(root_dir, output_file="inventaire_stl.md"):
    base_path = Path(root_dir)
    if not base_path.exists():
        print(f"Erreur : Le dossier '{root_dir}' n'existe pas.")
        return

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Inventaire des fichiers STL\n\n")

        # --- SECTION 1 : Tableaux par dossier de premier niveau ---
        f.write("## 1. Tableaux par dossier (Niveau 1)\n\n")
        
        # On ne prend que les dossiers directs à la racine
        top_folders = [d for d in base_path.iterdir() if d.is_dir()]
        
        for folder in sorted(top_folders):
            # Recherche récursive des STL dans ce dossier spécifique
            stl_files = list(folder.rglob("*.stl"))
            
            if stl_files:
                f.write(f"### Dossier : `{folder.name}`\n\n")
                f.write("| Nom du fichier | Chemin relatif | Taille (Ko) |\n")
                f.write("| :--- | :--- | :--- |\n")
                
                for stl in sorted(stl_files):
                    rel_path = stl.relative_to(base_path)
                    size = round(stl.stat().st_size / 1024, 2)
                    f.write(f"| {stl.name} | `{rel_path}` | {size} |\n")
                f.write("\n")

        # --- SECTION 2 : Tableau Multi-niveaux Global ---
        f.write("## 2. Inventaire Complet Multi-niveaux\n\n")
        f.write("| Dossier Parent | Fichier STL | Chemin Complet |\n")
        f.write("| :--- | :--- | :--- |\n")
        
        # Parcours de toute l'arborescence
        all_stls = sorted(list(base_path.rglob("*.stl")))
        for stl in all_stls:
            parent_name = stl.parent.name if stl.parent != base_path else "Racine"
            rel_path = stl.relative_to(base_path)
            f.write(f"| **{parent_name}** | {stl.name} | `{rel_path}` |\n")

    print(f"Succès ! Le fichier '{output_file}' a été généré.")

# Utilisation : remplacez '.' par le chemin de votre dossier
generate_stl_markdown('.')
