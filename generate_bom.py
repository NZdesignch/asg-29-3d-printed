import json
import shutil
import subprocess
import urllib.parse
from pathlib import Path

# --- CONFIGURATION DES CONSTANTES ---
OUTPUT_FILE = "bom.md"             # Nom du fichier Markdown de sortie
SETTINGS_FILE = "print_settings.json"  # Fichier stockant les paramètres d'impression
EXCLUDE = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives'} # Dossiers à ignorer
COMMON_KEYS = [                    # Paramètres globaux à extraire du JSON
    "top_solid_layers", "bottom_solid_layers", 
    "fill_density", "fill_pattern", 
    "infill_anchor", "infill_anchor_max"
]

def get_raw_url():
    """
    Récupère l'URL de base pour les fichiers 'raw' sur GitHub.
    Permet de créer des liens de téléchargement direct.
    """
    try:
        # Interroge Git pour connaître l'URL du dépôt distant
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        # Nettoie l'URL pour passer d'un format Git/HTTPS à un format raw content
        repo = url.replace("https://github.com/", "").replace("git@github.com:", "").replace(".git", "")
        return f"https://raw.githubusercontent.com/{repo}/main"
    except Exception:
        # Si on n'est pas dans un dépôt Git, les liens pointeront vers le local
        return "."

def check(v):
    """
    Formate une valeur pour le Markdown. 
    Affiche un cercle rouge si la donnée est manquante dans le JSON.
    """
    if v is not None and str(v).strip() != "":
        return f"**{v}**"
    return "🔴 _À définir_"

def generate_bom():
    """Fonction principale de génération de la Nomenclature."""
    root = Path(".")
    archive_dir = root / "archives"
    archive_dir.mkdir(exist_ok=True) # Crée le dossier archives s'il n'existe pas
    
    settings_path = root / SETTINGS_FILE
    raw_url = get_raw_url()
    
    # --- 1. CHARGEMENT ET RÉCUPÉRATION DES DONNÉES ---
    existing_data = {}
    if settings_path.exists():
        try:
            # Charge les réglages existants pour ne pas les écraser
            existing_data = json.loads(settings_path.read_text(encoding="utf-8"))
        except Exception:
            print(f"⚠️ Erreur de lecture {SETTINGS_FILE}.")

    # Prépare le dictionnaire qui sera sauvegardé à la fin (pour mise à jour)
    new_data = {"COMMON_SETTINGS": {}}
    old_common = existing_data.get("COMMON_SETTINGS", {})
    for k in COMMON_KEYS:
        new_data["COMMON_SETTINGS"][k] = old_common.get(k)

    # --- 2. ANALYSE DE LA STRUCTURE DES DOSSIERS ---
    sections = []
    # Scanne les dossiers de niveau 1 (ex: MTL, Avion...)
    level1_dirs = sorted([d for d in root.iterdir() if d.is_dir() and d.name not in EXCLUDE])
    for l1 in level1_dirs:
        # Scanne les sous-dossiers (les "modules")
        for m in sorted([d for d in l1.iterdir() if d.is_dir()]):
            # On n'ajoute le module que s'il contient au moins un fichier STL
            if any(m.rglob("*.stl")):
                sections.append((m, l1.name))

    # --- 3. DÉBUT DE RÉDACTION DU MARKDOWN (Sommaire & Paramètres) ---
    md = ["# 🛠️ Nomenclature (BOM)\n", "## 📌 Sommaire"]
    
    # Génère les ancres du sommaire
    for mod_path, _ in sections:
        clean_name = mod_path.name.replace('_', ' ').capitalize()
        anchor = mod_path.name.lower().replace(" ", "-").replace("_", "-")
        md.append(f"- [{clean_name}](#-{anchor})")
    
    # Tableau des paramètres communs (récupérés du haut du JSON)
    c = new_data["COMMON_SETTINGS"]
    md.extend([
        "\n---\n", "## ⚙️ Paramètres d'Impression Généraux\n",
        "| Paramètre | Valeur |", "| :--- | :--- |",
        f"| Couches Solides | {check(c.get('top_solid_layers'))} / {check(c.get('bottom_solid_layers'))} |",
        f"| Remplissage | {check(c.get('fill_density'))} / {check(c.get('fill_pattern'))} |",
        f"| Ancre de remplissage | {check(c.get('infill_anchor'))} / {check(c.get('infill_anchor_max'))} |\n",
        "---"
    ])

    # --- 4. GÉNÉRATION DES TABLEAUX PAR MODULE (PIÈCES STL) ---
    for mod, parent in sections:
        # Crée une archive ZIP pour le module complet
        safe_zip_name = mod.name.replace(" ", "_")
        zip_filename = f"module_{safe_zip_name}"
        shutil.make_archive(str(archive_dir / zip_filename), 'zip', root_dir=mod)
        
        clean_title = mod.name.replace('_', ' ').capitalize()
        encoded_zip = urllib.parse.quote(zip_filename)
        zip_url = f"{raw_url}/archives/{encoded_zip}.zip"
        
        # En-tête de la section du module
        md.extend([
            f"\n## 📦 {clean_title}",
            f"Section : `{parent}` | **[🗜️ Télécharger ZIP]({zip_url})**\n",
            "| Structure | État | Périmètres | Vue 3D | Download |",
            "| :--- | :---: | :---: | :---: | :---: |"
        ])

        # Scanne tous les fichiers et dossiers à l'intérieur du module
        for item in sorted(mod.rglob("*")):
            # Ignore les fichiers qui ne sont pas des dossiers ou des STL
            if not (item.is_dir() or item.suffix.lower() == ".stl"):
                continue
                
            rel_path = str(item.relative_to(root))
            # Gère l'indentation visuelle selon la profondeur des sous-dossiers
            depth = len(item.relative_to(mod).parts)
            indent = "&nbsp;" * 4 * depth + "/ " if depth > 0 else ""
            
            if item.suffix.lower() == ".stl":
                # Récupère le nombre de périmètres dans le JSON
                old_val = existing_data.get(rel_path, {}).get("perimeters")
                new_data[rel_path] = {"perimeters": old_val} # Prépare pour la sauvegarde
                
                status = "🟢" if old_val is not None else "🔴"
                display_perim = old_val if old_val is not None else "---"
                u_path = urllib.parse.quote(rel_path) # Encode l'URL (espaces, accents...)
                
                # Ajoute la ligne de la pièce au tableau
                md.append(f"| {indent}📄 {item.name} | {status} | {display_perim} | [👁️]({u_path}) | [💾]({raw_url}/{u_path}) |")
            else:
                # Ajoute une ligne pour un sous-dossier
                md.append(f"| {indent}📂 **{item.name}** | - | - | - | - |")
        
        # Pied de section
        md.append("\n[⬆️ Retour au sommaire](#-sommaire)\n\n---")

    # --- 5. SAUVEGARDE ET EXPORT ---
    # Écrit le fichier Markdown final
    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    # Met à jour le JSON (ajoute les nouveaux fichiers trouvés avec périmètres à null)
    Path(SETTINGS_FILE).write_text(json.dumps(new_data, indent=4, ensure_ascii=False), encoding="utf-8")
    print("✅ BOM généré avec succès.")

if __name__ == "__main__":
    generate_bom()
