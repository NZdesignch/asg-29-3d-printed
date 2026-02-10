import os
import re

target_extension = ".stl"
output_file = "BOM.md"
base_folder = "stl" # Le dossier racine contenant tes catégories

def generate_markdown_bom(base_dir):
    if not os.path.exists(base_dir):
        return f"Erreur : Le dossier '{base_dir}' est introuvable."

    markdown_output = f"# ✈️ Nomenclature ASG 29 (BOM)\n\n"
    
    # On récupère uniquement les dossiers de 1er niveau (Aile, Fuselage, etc.)
    categories = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])

    for category in categories:
        category_path = os.path.join(base_dir, category)
        markdown_output += f"## 📦 {category.upper()}\n\n"
        
        # En-tête du tableau pour cette catégorie
        markdown_output += "| Structure / Fichier | Qté | Lien |\n"
        markdown_output += "| :--- | :---: | :---: |\n"
        
        # Parcours de la catégorie
        for root, dirs, files in os.walk(category_path):
            stl_files = [f for f in files if f.lower().endswith(target_extension)]
            
            if stl_files:
                # Calcul du chemin relatif par rapport à la catégorie pour l'indentation
                rel_to_category = os.path.relpath(root, category_path).replace("\\", "/")
                
                # Si on est dans un sous-dossier, on ajoute une ligne intercalaire
                if rel_to_category != ".":
                    depth = rel_to_category.count('/')
                    indent = "&nbsp;&nbsp;" * depth + "└── 📁 "
                    markdown_output += f"| **{indent}{os.path.basename(root)}** | | |\n"
                
                # Ajout des fichiers STL
                for stl in sorted(stl_files):
                    qty_match = re.search(r'(?:x|qty|v)?(\d+)', stl, re.I)
                    qty = qty_match.group(1) if qty_match else "1"
                    
                    # Indentation des fichiers
                    file_depth = 0 if rel_to_category == "." else rel_to_category.count('/') + 1
                    file_indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * file_depth + "📄 "
                    
                    # Chemin complet pour le lien GitHub
                    full_rel_path = os.path.relpath(os.path.join(root, stl), ".").replace("\\", "/")
                    
                    markdown_output += f"| {file_indent}{stl} | {qty} | [Ouvrir]({full_rel_path}) |\n"
        
        markdown_output += "\n---\n\n" # Séparateur entre les tableaux
            
    return markdown_output

if __name__ == "__main__":
    content = generate_markdown_bom(base_folder)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ BOM généré avec des tableaux séparés par catégorie.")
