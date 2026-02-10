import os
import re
import json
import urllib.parse

# --- CONFIGURATION DU PROJET ---
# Dossier contenant les fichiers STL
BASE_DIR = "stl"
# Fichiers de sortie
OUTPUT_MD = "BOM.md"
SETTINGS_JSON = "print_settings.json"
# Informations de ton dépôt GitHub
REPO_URL = "https://github.com"
BRANCH = "main"

# Liste des paramètres d'impression à suivre dans le JSON
FIELDS = [
    "perimetres", "couches_dessus", "couches_dessous", 
    "remplissage", "motif_remplissage", "longueur_ancre", "longueur_max_ancre"
]

def load_json_data():
    """Charge le fichier JSON s'il existe, sinon renvoie un dictionnaire vide."""
    if os.path.exists(SETTINGS_JSON):
        with open(SETTINGS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json_data(data):
    """Sauvegarde les données dans le fichier JSON avec indentation pour lisibilité."""
    with open(SETTINGS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def generate_bom():
    # 1. Préparation des données
    db = load_json_data()
    markdown = [f"# ✈️ Nomenclature ASG 29\n\n> `🟢` Configuré | `🔴` En attente de paramètres dans `{SETTINGS_JSON}`\n"]

    # 2. Liste les catégories (dossiers de 1er niveau dans 'stl/')
    # Exemple : 'Ailes', 'Fuselage', 'Empennage'
    categories = sorted([d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))])

    for cat in categories:
        cat_path = os.path.join(BASE_DIR, cat)
        markdown.append(f"## 📦 {cat.upper()}\n")
        
        # En-tête du tableau Markdown
        header = ("| Statut | Pièce | Qté | Paramètres d'impression | Voir | STL |\n"
                  "| :---: | :--- | :---: | :--- | :---: | :---: |")
        markdown.append(header)

        # 3. Parcours récursif de la catégorie
        for root, _, files in os.walk(cat_path):
            stls = sorted([f for f in files if f.lower().endswith(".stl")])
            if not stls: continue

            # Gestion de la hiérarchie (sous-dossiers)
            rel_path = os.path.relpath(root, cat_path).replace("\\", "/")
            if rel_path != ".":
                depth = rel_path.count('/')
                indent = "&nbsp;&nbsp;" * (depth * 2) + "└── 📁 "
                markdown.append(f"| | **{indent}{os.path.basename(root)}** | | | | |")

            # 4. Traitement de chaque fichier STL
            for stl in stls:
                full_path = os.path.join(root, stl).replace("\\", "/")
                
                # Récupère ou crée l'entrée dans le JSON
                info = db.setdefault(full_path, {f: None for f in FIELDS})
                
                # Vérifie si tous les champs sont remplis (pas de None ni de vide)
                is_ok = all(info.get(f) not in [None, ""] for f in FIELDS)
                status = "🟢" if is_ok else "🔴"
                
                # Extraction auto de la quantité (ex: 'aile_x2.stl' -> 2)
                qty = (re.findall(r'[xX](\d+)', stl) + ["1"])[0]
                
                # Formatage des paramètres d'impression pour le tableau
                p = info
                params = (f"`{p['perimetres'] or '-'}`P | "
                          f"`{p['couches_dessus'] or '-'}↑{p['couches_dessous'] or '-'}↓` | "
                          f"`{p['remplissage'] or '-'}% ({p['motif_remplissage'] or '-'})` | "
                          f"`{p['longueur_ancre'] or '-'}➜{p['longueur_max_ancre'] or '-'}`")

                # Génération des liens GitHub (Vue 3D et Téléchargement Direct)
                encoded_path = urllib.parse.quote(full_path)
                url_view = f"{REPO_URL}/blob/{BRANCH}/{encoded_path}"
                url_raw = f"{REPO_URL}/raw/{BRANCH}/{encoded_path}"

                # Indentation visuelle du fichier dans l'arborescence
                file_depth = 0 if rel_path == "." else rel_path.count('/') + 1
                file_indent = "&nbsp;&nbsp;" * (file_depth * 4) + "📄 "

                # Ajout de la ligne au tableau
                line = (f"| {status} | {file_indent}<samp>{stl}</samp> | `x{qty}` | "
                        f"{params} | [👁️]({url_view}) | [📥]({url_raw}) |")
                markdown.append(line)

        markdown.append("\n---\n") # Séparateur entre les sections

    # 5. Écriture finale des fichiers
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown))
    
    save_json_data(db)
    print(f"✅ BOM généré avec succès dans {OUTPUT_MD}")
    print(f"📝 Paramètres d'impression synchronisés dans {SETTINGS_JSON}")

if __name__ == "__main__":
    generate_bom()
