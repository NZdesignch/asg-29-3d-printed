import os
import json
import shutil
import subprocess
from pathlib import Path
import urllib.parse

def get_github_repo_info():
    """
    Récupère dynamiquement l'URL 'raw' de ton dépôt GitHub.
    C'est ce qui permet aux liens de téléchargement (💾) de fonctionner directement.
    """
    try:
        # On demande à git l'URL du dépôt distant
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"]).decode().strip()
        # On nettoie l'URL pour extraire 'Utilisateur/Depot'
        repo_path = remote_url.replace("https://github.com", "").replace(".git", "").replace("git@github.com:", "")
        # On pointe sur la branche 'main' pour les fichiers bruts (raw)
        return f"https://raw.githubusercontent.com{repo_path}/main"
    except Exception:
        # Si on est en local sans git, on retourne le dossier courant
        return "."

def generate_bom():
    # --- CONFIGURATION DES CHEMINS ---
    root_dir = Path(".")
    output_file = "bom.md"
    settings_file = "print_settings.json"
    archive_dir = Path("archives")
    # On ignore les dossiers techniques et le dossier d'archives lui-même
    exclude = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives'}
    
    # Création du dossier qui contiendra les fichiers ZIP
    archive_dir.mkdir(exist_ok=True)
    base_raw_url = get_github_repo_info()

    # --- 1. LECTURE ET PROTECTION DU JSON ---
    existing_data = {}
    if Path(settings_file).exists():
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                # On charge le JSON actuel pour récupérer tes réglages manuels
                existing_data = json.load(f)
        except Exception as e:
            # SÉCURITÉ : Si le JSON a une erreur de virgule, on arrête tout pour ne rien effacer
            print(f"❌ Erreur lecture JSON: {e}")
            return 

    # --- 2. SYNCHRONISATION DES PARAMÈTRES COMMUNS ---
    # Liste exacte des clés que l'on veut dans le récapitulatif
    common_keys = [
        "top_solid_layers", "bottom_solid_layers", 
        "fill_density", "fill_pattern", 
        "infill_anchor", "infill_anchor_max"
    ]
    
    # On prépare le nouveau dictionnaire en récupérant les valeurs du JSON
    new_data = {"COMMON_SETTINGS": {}}
    current_common = existing_data.get("COMMON_SETTINGS", {})
    
    for k in common_keys:
        # On garde la valeur si elle existe, sinon on laisse à None (🔴 À définir)
        new_data["COMMON_SETTINGS"][k] = current_common.get(k)

    # Variable pratique pour l'écriture du tableau Markdown plus bas
    common = new_data["COMMON_SETTINGS"]

    # --- 3. ANALYSE DE L'ARBORESCENCE ---
    # On cherche les dossiers de niveau 1 (ex: MTL) puis de niveau 2 (ex: Aile_Gauche)
    level1_dirs = sorted([d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude])
    modules_list = []
    for l1 in level1_dirs:
        l2_dirs = sorted([d for d in l1.iterdir() if d.is_dir()])
        for m in l2_dirs:
            # On ne prend que les dossiers qui contiennent des fichiers STL
            if list(m.rglob("*.stl")):
                modules_list.append((m, l1.name))

    # --- 4. ÉCRITURE DU FICHIER bom.md ---
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ Nomenclature (BOM)\n\n")

        # GÉNÉRATION DU SOMMAIRE CLIQUABLE
        f.write("## 📌 Sommaire\n")
        for mod_path, _ in modules_list:
            # Création d'une ancre (lien interne) compatible GitHub
            anchor = mod_path.name.lower().replace(" ", "-").replace("_", "-")
            f.write(f"- [Module : {mod_path.name.replace('_', ' ')}](#-module--{anchor})\n")
        f.write("\n---\n\n")

        # TABLEAU DES PARAMÈTRES GÉNÉRAUX (Se met à jour via le JSON)
        f.write("## ⚙️ Paramètres d'Impression Généraux\n\n")
        def check(val): 
            # Si vide ou None, on affiche l'alerte rouge
            if val is None or str(val).strip() == "":
                return "🔴 _À définir_"
            # Sinon on affiche la valeur en gras pour confirmer la prise en compte
            return f"**{val}**"

        f.write("| Paramètre | Valeur |\n")
        f.write("| :--- | :--- |\n")
        f.write(f"| Couches Solides (Dessus / Dessous) | {check(common['top_solid_layers'])} / {check(common['bottom_solid_layers'])} |\n")
        f.write(f"| Remplissage (Densité / Motif) | {check(common['fill_density'])} / {check(common['fill_pattern'])} |\n")
        f.write(f"| Ancre de remplissage (Valeur / Max) | {check(common['infill_anchor'])} / {check(common['infill_anchor_max'])} |\n\n")
        
        f.write("---\n\n")

        # GÉNÉRATION DES TABLEAUX PAR MODULE
        for module_path, parent_name in modules_list:
            # Création de l'archive ZIP pour ce module (ex: module_aile_gauche.zip)
            safe_name = module_path.name.replace(" ", "_")
            zip_filename = f"module_{safe_name}"
            shutil.make_archive(str(archive_dir / zip_filename), 'zip', root_dir=module_path)
            
            # Écriture du titre du module avec lien ZIP
            f.write(f"## 📦 Module : {module_path.name.replace('_', ' ')}\n")
            f.write(f"Section : `{parent_name}` | **[🗜️ Télécharger ZIP]({base_raw_url}/archives/{urllib.parse.quote(zip_filename)}.zip)**\n\n")
            
            # Entête du tableau des pièces
            f.write("| Structure | État | Périmètres | Vue 3D | Download |\n| :--- | :---: | :---: | :---: | :---: |\n")

            # Parcours de tous les fichiers à l'intérieur du module
            for item in sorted(list(module_path.rglob("*"))):
                if item.is_dir() or item.suffix.lower() == ".stl":
                    rel_path = str(item.relative_to(root_dir))
                    # Indentation visuelle (le petit slash / )
                    depth = len(item.relative_to(module_path).parts)
                    indent = "&nbsp;" * 4 * depth + "/ " if depth > 0 else ""
                    
                    if item.suffix.lower() == ".stl":
                        # RÉCUPÉRATION : On garde la valeur perimeters si elle existe déjà
                        old_perim = existing_data.get(rel_path, {}).get("perimeters")
                        new_data[rel_path] = {"perimeters": old_perim}
                        
                        status = "🟢" if old_perim is not None else "🔴"
                        per = old_perim if old_perim is not None else "---"
                        url_path = urllib.parse.quote(rel_path)
                        
                        f.write(f"| {indent}📄 {item.name} | {status} | {per} | [👁️]({url_path}) | [💾]({base_raw_url}/{url_path}) |\n")
                    else:
                        # C'est un dossier interne au module
                        f.write(f"| {indent}📂 **{item.name}** | - | - | - | - |\n")
            
            # Lien de retour rapide en haut du document
            f.write("\n[⬆️ Retour au sommaire](#-sommaire)\n\n---\n\n")

    # --- 5. SAUVEGARDE FINALE DU JSON ---
    with open(settings_file, "w", encoding="utf-8") as f:
        # On réécrit le JSON proprement (indentation de 4 pour la lisibilité)
        json.dump(new_data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    generate_bom()
