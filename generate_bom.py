import os
import re
import json
import urllib.parse

# --- CONFIGURATION ---
target_extension = ".stl"
output_file = "BOM.md"
json_file = "print_settings.json"
base_folder = "stl"
repo_url = "https://github.com" # À MODIFIER
branch = "main"

FIELDS = [
    "perimetres", "couches_dessus", "couches_dessous", 
    "remplissage", "motif_remplissage", "longueur_ancre", "longueur_max_ancre"
]

def load_settings():
    if os.path.exists(json_file):
        with open(json_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_settings(settings):
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

def generate_markdown_bom(base_dir):
    settings = load_settings()
    new_settings = settings.copy()
    
    markdown_output = f"# ✈️ Nomenclature ASG 29\n\n"
    markdown_output += "> `🟢` Configuré | `🔴` Paramètres à renseigner dans `print_settings.json` \n\n"
    
    categories = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])

    for category in categories:
        category_path = os.path.join(base_dir, category)
        markdown_output += f"## 📦 {category.upper()}\n\n"
        
        # Colonnes séparées pour Voir et STL
        markdown_output += "| Statut | Pièce | Qté | Périm. | Haut/Bas | Rempl. (Motif) | Ancres | Voir | STL |\n"
        markdown_output += "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
        
        for root, dirs, files in os.walk(category_path):
            stl_files = [f for f in files if f.lower().endswith(target_extension)]
            if stl_files:
                rel_path = os.path.relpath(root, base_dir).replace("\\", "/")
                
                for stl in sorted(stl_files):
                    file_key = f"{base_folder}/{rel_path}/{stl}".replace("//", "/")
                    
                    if file_key not in new_settings:
                        new_settings[file_key] = {field: None for field in FIELDS}
                    
                    data = new_settings[file_key]
                    is_complete = all(data.get(f) is not None and data.get(f) != "" for f in FIELDS)
                    status_icon = "🟢" if is_complete else "🔴"
                    
                    qty_match = re.search(r'(?:x|qty|v)?(\d+)', stl, re.I)
                    qty = qty_match.group(1) if qty_match else "1"
                    
                    # Mise en forme des paramètres (Sans balises <small>)
                    perim = data.get("perimetres") or "-"
                    layers = f"{data.get('couches_dessus') or '-'}↑ {data.get('couches_dessous') or '-'}↓"
                    infill = f"{data.get('remplissage') or '-'} ({data.get('motif_remplissage') or '-'})"
                    anchors = f"{data.get('longueur_ancre') or '-'} ➜ {data.get('longueur_max_ancre') or '-'}"
                    
                    # Encodage et URLs
                    encoded_path = urllib.parse.quote(file_key)
                    view_url = f"{repo_url}/blob/{branch}/{encoded_path}"
                    dl_url = f"{repo_url}/raw/{branch}/{encoded_path}"
                    
                    # Liens séparés utilisant <samp> pour l'uniformité
                    view_link = f'[<samp>👁️ VUE</samp>]({view_url})'
                    dl_link = f'[<samp>📥 STL</samp>]({dl_url})'
                    
                    markdown_output += (f"| {status_icon} | <samp>{stl}</samp> | `x{qty}` | "
                                       f"`{perim}` | `{layers}` | `{infill}` | "
                                       f"`{anchors}` | {view_link} | {dl_link} |\n")
        
        markdown_output += "\n---\n\n"

    save_settings(new_settings)
    return markdown_output

if __name__ == "__main__":
    content = generate_markdown_bom(base_folder)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ BOM moderne généré avec colonnes d'actions séparées.")
