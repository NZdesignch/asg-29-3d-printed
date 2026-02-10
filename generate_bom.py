import os
import re

target_extension = ".stl"
output_file = "BOM.md"

def generate_markdown_bom(root_dir):
    markdown_output = "# ✈️ Nomenclature ASG 29 - Structure de Fabrication\n\n"
    markdown_output += "| Emplacement / Pièce | Qté | Lien | Note |\n"
    markdown_output += "| :--- | :---: | :---: | :--- |\n"
    
    # On trie les dossiers pour avoir un ordre logique
    for root, dirs, files in sorted(os.walk(root_dir)):
        if '.git' in root or root == '.': continue
        
        stl_files = [f for f in files if f.lower().endswith(target_extension)]
        
        if stl_files:
            # Calcul de la profondeur pour l'indentation visuelle
            relative_path = os.path.relpath(root, root_dir).replace("\\", "/")
            depth = relative_path.count('/')
            indent = "📂 " if depth == 0 else "&nbsp;&nbsp;&nbsp;&nbsp;" * depth + "└── 📁 "
            
            # Ligne de section pour le dossier
            folder_name = os.path.basename(root)
            markdown_output += f"| **{indent}{folder_name}** | | | |\n"
            
            for stl in sorted(stl_files):
                # Extraction quantité (ex: x2, 2x)
                qty_match = re.search(r'(?:x|qty|v)?(\d+)', stl, re.I)
                qty = qty_match.group(1) if qty_match else "1"
                
                # Lien et indentation du fichier
                file_path = f"{relative_path}/{stl}"
                file_indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * (depth + 1) + "📄 "
                
                markdown_output += f"| {file_indent}{stl} | {qty} | [Ouvrir]({file_path}) | |\n"
            
    return markdown_output

if __name__ == "__main__":
    # On cible le dossier 'stl' spécifié dans ta demande initiale
    content = generate_markdown_bom("stl") 
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ BOM multi-niveaux généré dans {output_file}")
