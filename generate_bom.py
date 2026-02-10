import os
import re
import urllib.parse

# --- CONFIGURATION ---
target_extension = ".stl"
output_file = "BOM.md"
base_folder = "stl"
repo_url = "https://github.com/NZdesignch" # À MODIFIER
branch = "main"
# ---------------------

def generate_markdown_bom(base_dir):
    if not os.path.exists(base_dir):
        return f"Erreur : Dossier '{base_dir}' introuvable."

    # Header avec police moderne via HTML
    markdown_output = f"# ✈️ Nomenclature ASG 29\n\n"
    markdown_output += "> *Génération automatique de la liste des pièces de fabrication.*\n\n"
    
    categories = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])

    for category in categories:
        category_path = os.path.join(base_dir, category)
        markdown_output += f"## 📦 {category.upper()}\n\n"
        
        # Table avec colonnes actions distinctes
        markdown_output += "| Pièce | Qté | Vue 3D | Fichier |\n"
        markdown_output += "| :--- | :---: | :---: | :---: |\n"
        
        for root, dirs, files in os.walk(category_path):
            stl_files = [f for f in files if f.lower().endswith(target_extension)]
            
            if stl_files:
                rel_to_cat = os.path.relpath(root, category_path).replace("\\", "/")
                
                if rel_to_cat != ".":
                    depth = rel_to_cat.count('/')
                    indent = "&nbsp;&nbsp;" * depth + "└── 📁 "
                    markdown_output += f"| **{indent}{os.path.basename(root)}** | | | |\n"
                
                for stl in sorted(stl_files):
                    qty = re.search(r'(?:x|qty|v)?(\d+)', stl, re.I)
                    qty = qty.group(1) if qty else "1"
                    
                    file_depth = 0 if rel_to_cat == "." else rel_to_cat.count('/') + 1
                    file_indent = "&nbsp;&nbsp;&nbsp;&nbsp;" * file_depth + "📄 "
                    
                    # Encodage URL
                    rel_file_path = os.path.relpath(os.path.join(root, stl), ".").replace("\\", "/")
                    encoded_path = urllib.parse.quote(rel_file_path)
                    
                    # --- STYLE MODERNE UNIFORMISÉ ---
                    # On utilise <samp> pour une police technique propre et uniforme
                    name_display = f"{file_indent}<samp>{stl}</samp>"
                    qty_display = f"<code>{qty}</code>"
                    
                    # Boutons "Interface"
                    view_url = f"{repo_url}/blob/{branch}/{encoded_path}"
                    view_btn = f'[<samp>👁️ Visualiser</samp>]({view_url})'
                    
                    dl_url = f"{repo_url}/raw/{branch}/{encoded_path}"
                    dl_btn = f'[<samp>📥 Télécharger</samp>]({dl_url})'
                    
                    markdown_output += f"| {name_display} | {qty_display} | {view_btn} | {dl_btn} |\n"
        
        markdown_output += "\n"
            
    return markdown_output

if __name__ == "__main__":
    content = generate_markdown_bom(base_folder)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"🚀 BOM moderne et uniforme généré dans {output_file}")
