import os
import json
import subprocess
from pathlib import Path
import urllib.parse

def get_github_repo_info():
    """
    Récupère dynamiquement l'URL 'raw' de GitHub pour permettre le téléchargement direct.
    Transforme l'URL du dépôt en lien compatible avec raw.githubusercontent.com.
    """
    try:
        # On utilise la commande git pour obtenir l'URL du dépôt distant (origin)
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"]).decode().strip()
        # Nettoyage de l'URL pour extraire 'Utilisateur/Depot'
        repo_path = remote_url.replace("https://github.com", "").replace(".git", "").replace("git@github.com:", "")
        # On cible la branche 'main' (à changer en 'master' si nécessaire)
        return f"https://raw.githubusercontent.com{repo_path}/main"
    except:
        # En cas d'erreur (ex: exécution locale sans git), on retourne le chemin relatif
        return "."

def generate_bom():
    # --- CONFIGURATION DES CHEMINS ---
    root_dir = Path(".")
    output_file = "bom.md"
    settings_file = "print_settings.json"
    # Dossiers à ignorer lors du scan pour éviter de polluer la nomenclature
    exclude = {'.git', '.github', '__pycache__', 'venv', '.vscode'}
    
    # URL de base pour les liens de téléchargement direct 💾
    base_raw_url = get_github_repo_info()

    # --- CHARGEMENT DU FICHIER DE PARAMÈTRES (JSON) ---
    if Path(settings_file).exists():
        with open(settings_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    # Liste des clés partagées entre toutes les pièces
    common_keys = [
        "top_solid_layers", "bottom_solid_layers", 
        "fill_density", "fill_pattern", 
        "infill_anchor", "infill_anchor_max"
    ]
    
    # Initialisation de la section 'COMMON_SETTINGS' si elle est absente
    if "COMMON_SETTINGS" not in data:
        data["COMMON_SETTINGS"] = {k: None for k in common_keys}
    
    common = data["COMMON_SETTINGS"]
    # On crée un nouveau dictionnaire pour 'nettoyer' le JSON final
    new_print_settings = {"COMMON_SETTINGS": common}

    # --- PRÉPARATION DES MODULES (NIVEAU 2) ---
    # On scanne les dossiers de niveau 1 (ex: MTL) puis de niveau 2 (ex: Aile_Gauche)
    level1_dirs = sorted([d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude])
    modules_list = []
    for l1 in level1_dirs:
        l2_dirs = sorted([d for d in l1.iterdir() if d.is_dir()])
        for m in l2_dirs:
            # On n'ajoute au sommaire que les dossiers contenant au moins un fichier STL
            if list(m.rglob("*.stl")):
                modules_list.append((m.name, l1.name))

    # --- ÉCRITURE DU FICHIER MARKDOWN (bom.md) ---
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ Nomenclature (BOM)\n\n")

        # 1. GÉNÉRATION DU SOMMAIRE DYNAMIQUE
        f.write("## 📌 Sommaire\n")
        for mod_name, _ in modules_list:
            # Création d'une ancre compatible GitHub (minuscules et tirets)
            anchor = mod_name.lower().replace(" ", "-").replace("_", "-")
            f.write(f"- [Module : {mod_name.replace('_', ' ')}](#-module--{anchor})\n")
        f.write("\n---\n\n")

        # 2. TABLEAU DES PARAMÈTRES COMMUNS (Textuel, sans icônes)
        f.write("## ⚙️ Paramètres d'Impression Généraux\n\n")
        # Fonction simple pour afficher un indicateur si la valeur est manquante
        def check(val): return val if val is not None else "🔴 _À définir_"
        
        f.write("| Paramètre | Valeur |\n| :--- | :--- |\n")
        f.write(f"| Couches Solides (Dessus / Dessous) | {check(common['top_solid_layers'])} / {check(common['bottom_solid_layers'])} |\n")
        f.write(f"| Remplissage (Densité / Motif) | {check(common['fill_density'])} / {check(common['fill_pattern'])} |\n")
        f.write(f"| Ancre de remplissage (Valeur / Max) | {check(common['infill_anchor'])} / {check(common['infill_anchor_max'])} |\n\n")
        f.write("---\n\n")

        # 3. GÉNÉRATION DES TABLEAUX PAR MODULE
        for l1 in level1_dirs:
            level2_dirs = sorted([d for d in l1.iterdir() if d.is_dir()])
            for module in level2_dirs:
                stls = sorted(list(module.rglob("*.stl")))
                if not stls: continue

                f.write(f"## 📦 Module : {module.name.replace('_', ' ')}\n")
                f.write(f"Section : `{l1.name}`\n\n")
                f.write("| Structure | État | Périmètres | Vue 3D | Download |\n| :--- | :---: | :---: | :---: | :---: |\n")

                # On parcourt récursivement tous les fichiers et sous-dossiers du module
                for item in sorted(list(module.rglob("*"))):
                    if item.is_dir() or item.suffix.lower() == ".stl":
                        rel_path = str(item.relative_to(root_dir))
                        # Calcul de l'indentation visuelle avec des slashs
                        depth = len(item.relative_to(module).parts)
                        indent = "&nbsp;" * 4 * depth + "/ " if depth > 0 else ""
                        
                        status, per, view, dl = ["-"] * 4
                        
                        if item.suffix.lower() == ".stl":
                            # Récupération de la valeur périmètre existante ou initialisation à None
                            old_val = data.get(rel_path, {}).get("perimeters", None)
                            new_print_settings[rel_path] = {"perimeters": old_val}
                            
                            # Indicateur de complétion
                            status = "🟢" if old_val is not None else "🔴"
                            per = old_val if old_val is not None else "---"
                            
                            # Encodage du chemin pour les liens GitHub (gestion des espaces)
                            url_path = urllib.parse.quote(rel_path)
                            # Lien vers le viewer 3D natif de GitHub
                            view = f"[👁️]({url_path})"
                            # Lien de téléchargement direct via raw.githubusercontent.com
                            dl = f"[💾]({base_raw_url}/{url_path})"

                        icon = "📂" if item.is_dir() else "📄"
                        name = f"**{item.name}**" if item.is_dir() else item.name
                        f.write(f"| {indent}{icon} {name} | {status} | {per} | {view} | {dl} |\n")
                
                # Ajout d'un lien de retour rapide au sommaire
                f.write("\n[⬆️ Retour au sommaire](#-sommaire)\n\n---\n\n")

    # --- SAUVEGARDE DU JSON NETTOYÉ ---
    with open(settings_file, "w", encoding="utf-8") as f:
        # Indent=4 rend le fichier JSON facile à éditer manuellement sur GitHub
        json.dump(new_print_settings, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    generate_bom()
