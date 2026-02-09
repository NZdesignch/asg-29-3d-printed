import os

# Configuration
target_extension = ".stl"
output_file = "BOM.md"

def generate_markdown_bom(root_dir):
    markdown_output = "# Nomenclature des fichiers (BOM)\n\n"
    
    # Parcours récursif de l'arborescence
    for root, dirs, files in os.walk(root_dir):
        # On ne garde que les fichiers qui nous intéressent
        stl_files = [f for f in files if f.lower().endswith(target_extension)]
        
        if stl_files:
            # Création du titre basé sur le nom du dossier (relatif)
            relative_path = os.path.relpath(root, root_dir)
            folder_name = "Racine" if relative_path == "." else relative_path
            
            markdown_output += f"## 📂 Dossier : {folder_name}\n\n"
            
            # Création du tableau
            markdown_output += "| Fichier | Quantité | Note |\n"
            markdown_output += "| :--- | :---: | :--- |\n"
            
            for stl in sorted(stl_files):
                # On peut essayer d'extraire une quantité si le nom contient "x2" par exemple
                markdown_output += f"| {stl} | 1 | |\n"
            
            markdown_output += "\n---\n\n"
            
    return markdown_output

# Exécution
if __name__ == "__main__":
    content = generate_markdown_bom(".")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ Fichier {output_file} généré avec succès !")
