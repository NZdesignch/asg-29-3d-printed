import os
import re

target_extension = ".stl"
output_file = "BOM.md"

def generate_markdown_bom(base_dir):
    markdown_output = "# ✈️ Nomenclature ASG 29\n\n"
    
    # On liste les dossiers de 1er niveau
    first_level_dirs = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and not d.startswith('.')])

    for main_dir in first_level_dirs:
        main_path = os.path.join(base_dir, main_dir)
        markdown_output += f"## 📦 Section : {main_dir.upper()}\n\n"
        
        # Initialisation du tableau pour ce dossier principal
        table_header = "| Structure / Fichier | Qté | Lien |\n| :--- | :---: | :---: |\n"
        table_content = ""
        
        for root, dirs, files in os.walk(main_path):
            stl_files = [f for f in files if f.lower().endswith(target_extension)]
            
            if stl_files:
                rel_to_main = os.path.relpath(root, main_path).replace("\\", "/")
                rel_to_base = os.path.relpath(root, base_dir).replace("\\", "/")
                
                # Si on est dans un sous-dossier (niveau 2+), on crée une ligne de sous-titre dans le tableau
                if rel_to_main != ".":
                    depth = rel_to_main.count('/')
                    indent = "📂 " if depth == 0 else "&nbsp;&nbsp;" * depth + "└── 📁 "
                    table_content += f"| **{indent}{os.path.basename(root)}** | | |\n"
                
                # Ajout des fichiers
                for stl in sorted(stl_files):
                    qty_match = re.search(r'(?:x|qty|v)?(\d+)', stl, re.I)
                    qty = qty_match.group(1) if qty_match else "1"
                    
                    # Indentation des fichiers dans le tableau
                    file_indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * (rel_to_main.count('/') + 1) + "📄 " if rel_to_main != "." else "📄 "
                    link = f"[Ouvrir]({base_dir}/{rel_to_base}/{stl})"
                    
                    table_content += f"| {file_indent}{stl} | {qty} | {link} |\n"

        if table_content:
            markdown_output += table_header + table_content + "\n\n---\n\n"
            
    return markdown_output

if __name__ == "__main__":
    # On suppose que tes dossiers sont dans le répertoire 'stl/'
    content = generate_markdown_bom("stl")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ BOM structuré généré dans {output_file}")
