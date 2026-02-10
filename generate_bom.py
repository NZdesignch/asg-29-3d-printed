import os
import re

# --- CONFIGURATION ---
target_extension = ".stl"
output_file = "BOM.md"
base_folder = "stl"
# Remplace par ton URL GitHub (ex: "https://github.com")
repo_url = "https://github.com" 
# ---------------------

def generate_markdown_bom(base_dir):
    if not os.path.exists(base_dir):
        return f"Erreur : Le dossier '{base_dir}' est introuvable."

    markdown_output = f"# ✈️ Nomenclature ASG 29 (BOM)\n\n"
    categories = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])

    for category in categories:
        category_path = os.path.join(base_dir, category)
        markdown_output += f"## 📦 {category.upper()}\n\n"
        
        # En-tête avec les nouvelles colonnes
        markdown_output += "| Pièce | Qté | Vue 3D | Download |\n"
        markdown_output += "| :--- | :---: | :---: | :---: |\n"
        
        for root, dirs, files in os.walk(category_path):
            stl_files = [f for f in files if f.lower().endswith(target_extension)]
            
            if stl_files:
                rel_to_category = os.path.relpath(root, category_path).replace("\\", "/")
                
                if rel_to_category != ".":
                    depth = rel_to_category.count('/')
                    indent = "&nbsp;&nbsp;" * depth + "└── 📁 "
                    markdown_output += f"| **{indent}{os.path.basename(root)}** | | | |\n"
                
                for stl in sorted(stl_files):
                    qty_match = re.search(r'(?:x|qty|v)?(\d+)', stl, re.I)
                    qty = qty_match.group(1) if qty_match else "1"
                    
                    file_depth = 0 if rel_to_category == "." else rel_to_category.count('/') + 1
                    file_indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * file_depth + "📄 "
                    
                    # Chemins pour les liens
                    rel_file_path = os.path.relpath(os.path.join(root, stl), ".").replace("\\", "/")
                    
                    # Bouton Visualiser (Lien vers l'interface GitHub)
                    view_btn = f"[👁️ Voir]({rel_file_path})"
                    
                    # Bouton Télécharger (Lien vers le fichier RAW)
                    # GitHub format raw : repo_url + /raw/main/ + path
                    download_url = f"{repo_url}/raw/main/{rel_file_path}"
                    download_btn = f"[💾 Télécharger]({download_url})"
                    
                    markdown_output += f"| {file_indent}{stl} | {qty} | {view_btn} | {download_btn} |\n"
        
        markdown_output += "\n---\n\n"
            
    return markdown_output

if __name__ == "__main__":
    content = generate_markdown_bom(base_folder)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ BOM généré avec boutons interactifs !")
