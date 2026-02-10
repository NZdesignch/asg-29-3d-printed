import os
import re
import json
import urllib.parse

# --- CONFIGURATION ---
target_extension = ".stl"
output_file = "BOM.md"
json_file = "print_settings.json"
base_folder = "stl"
repo_url = "https://github.com" # À mettre à jour
branch = "main"

# Liste des paramètres à suivre
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
    markdown_output += "> `🟢` Configuré | `🔴` Paramètres manquants dans `print_settings.json` \n\n"
    
    categories = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])

    for category in categories:
        category_path = os.path.join(base_dir, category)
        markdown_output += f"## 📦 {category.upper()}\n\n"
        
        # En-tête large pour tous les paramètres
        markdown_output += "| Statut | Pièce | Qté | Périm. | Haut/Bas | Rempl. (Motif) | Ancres (Std/Max) | Actions |\n"
        markdown_output += "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |\n"
        
        for root, dirs, files in os.walk(category_path):
            stl_files = [f for f in files if f.lower().endswith(target_extension)]
            if stl_files:
                rel_path = os.path.relpath(root, base_dir).replace("\\", "/")
                
                for stl in sorted(stl_files):
                    file_key = f"{base_folder}/{rel_path}/{stl}".replace("//", "/")
                    
                    # Initialisation auto avec les 7 champs à null
                    if file_key not in new_settings:
                        new_settings[file_key] = {field: None for field in FIELDS}
                    
                    data = new_settings[file_key]
                    
                    # Vérification si tous les champs sont remplis
                    is_complete = all(data.get(f) is not None and data.get(f) != "" for f in FIELDS)
                    status_icon = "🟢" if is_complete else "🔴"
                    
                    # Extraction quantité
                    qty_match = re.search(r'(?:x|qty|v)?(\d+)', stl, re.I)
                    qty = qty_match.group(1) if qty_match else "1"
                    
                    # Préparation des données pour le tableau (affichage groupé pour lisibilité)
                    perim = data.get("perimetres") or "-"
                    layers = f"{data.get('couches_dessus') or '-'}/{data.get('couches_dessous') or '-'}"
                    infill = f"{data.get('remplissage') or '-'} ({data.get('motif_remplissage') or '-'})"
                    anchors = f"{data.get('longueur_ancre') or '-'} / {data.get('longueur_max_ancre') or '-'}"
                    
                    # Boutons
                    encoded_path = urllib.parse.quote(file_key)
                    view_url = f"{repo_url}/blob/{branch}/{encoded_path}"
                    dl_url = f"{repo_url}/raw/{branch}/{encoded_path}"
                    actions = f'[<samp>👁️</samp>]({view_url}) [<samp>📥</samp>]({dl_url})'
                    
                    markdown_output += (f"| {status_icon} | <samp>{stl}</samp> | `x{qty}` | "
                                       f"`{perim}` | `{layers}` | `<small>{infill}</small>` | "
                                       f"`<small>{anchors}</small>` | {actions} |\n")
        
        markdown_output += "\n---\n\n"

    save_settings(new_settings)
    return markdown_output

if __name__ == "__main__":
    content = generate_markdown_bom(base_folder)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"🚀 BOM ASG 29 généré avec {len(FIELDS)} paramètres d'impression.")
