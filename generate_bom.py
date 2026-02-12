import json
import shutil
import subprocess
import urllib.parse
from pathlib import Path

# --- CONFIGURATION ---
OUTPUT_FILE = "bom.md"
SETTINGS_FILE = "print_settings.json"
EXCLUDE = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives'}
COMMON_KEYS = [
    "top_solid_layers", "bottom_solid_layers", 
    "fill_density", "fill_pattern", 
    "infill_anchor", "infill_anchor_max"
]

def get_raw_url():
    """Récupère l'URL raw du dépôt GitHub."""
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        repo = url.replace("https://github.com/", "").replace("git@github.com:", "").replace(".git", "")
        return f"https://raw.githubusercontent.com/{repo}/main"
    except Exception:
        return "."

def check(v):
    """Vérifie si une valeur est définie pour l'affichage Markdown."""
    if v is not None and str(v).strip() != "":
        return f"**{v}**"
    return "🔴 _À définir_"

def generate_bom():
    root = Path(".")
    archive_dir = root / "archives"
    archive_dir.mkdir(exist_ok=True)
    
    settings_path = root / SETTINGS_FILE
    raw_url = get_raw_url()
    
    # 1. Chargement des données existantes
    existing_data = {}
    if settings_path.exists():
        try:
            existing_data = json.loads(settings_path.read_text(encoding="utf-8"))
        except Exception:
            print(f"⚠️ Erreur de lecture {SETTINGS_FILE}.")

    # Initialisation du nouveau dictionnaire
    new_data = {"COMMON_SETTINGS": {}}
    old_common = existing_data.get("COMMON_SETTINGS", {})
    for k in COMMON_KEYS:
        new_data["COMMON_SETTINGS"][k] = old_common.get(k)

    # 2. Analyse de l'arborescence
    sections = []
    level1_dirs = sorted([d for d in root.iterdir() if d.is_dir() and d.name not in EXCLUDE])
    for l1 in level1_dirs:
        for m in sorted([d for d in l1.iterdir() if d.is_dir()]):
            if any(m.rglob("*.stl")):
                sections.append((m, l1.name))

    # 3. Construction du contenu Markdown
    md = ["# 🛠️ Nomenclature (BOM)\n", "## 📌 Sommaire"]
    
    for mod_path, _ in sections:
        clean_name = mod_path.name.replace('_', ' ').capitalize()
        anchor = mod_path.name.lower().replace(" ", "-").replace("_", "-")
        md.append(f"- [{clean_name}](#-{anchor})")
    
    # Paramètres d'impression généraux
    c = new_data["COMMON_SETTINGS"]
    md.extend([
        "\n---\n", "## ⚙️ Paramètres d'Impression Généraux\n",
        "| Paramètre | Valeur |", "| :--- | :--- |",
        f"| Couches Solides | {check(c.get('top_solid_layers'))} / {check(c.get('bottom_solid_layers'))} |",
        f"| Remplissage | {check(c.get('fill_density'))} / {check(c.get('fill_pattern'))} |",
        f"| Ancre de remplissage | {check(c.get('infill_anchor'))} / {check(c.get('infill_anchor_max'))} |\n",
        "---"
    ])

    # 4. Génération des tableaux détaillés
    for mod, parent in sections:
        safe_zip_name = mod.name.replace(" ", "_")
        zip_filename = f"module_{safe_zip_name}"
        shutil.make_archive(str(archive_dir / zip_filename), 'zip', root_dir=mod)
        
        clean_title = mod.name.replace('_', ' ').capitalize()
        encoded_zip = urllib.parse.quote(zip_filename)
        zip_url = f"{raw_url}/archives/{encoded_zip}.zip"
        
        md.extend([
            f"\n## 📦 {clean_title}",
            f"Section : `{parent}` | **[🗜️ Télécharger ZIP]({zip_url})**\n",
            "| Structure | État | Périmètres | Vue 3D | Download |",
            "| :--- | :---: | :---: | :---: | :---: |"
        ])

        for item in sorted(mod.rglob("*")):
            if not (item.is_dir() or item.suffix.lower() == ".stl"):
                continue
                
            rel_path = str(item.relative_to(root))
            depth = len(item.relative_to(mod).parts)
            indent = "&nbsp;" * 4 * depth + "/ " if depth > 0 else ""
            
            if item.suffix.lower() == ".stl":
                old_val = existing_data.get(rel_path, {}).get("perimeters")
                new_data[rel_path] = {"perimeters": old_val}
                
                status = "🟢" if old_val is not None else "🔴"
                display_perim = old_val if old_val is not None else "---"
                u_path = urllib.parse.quote(rel_path)
                
                md.append(f"| {indent}📄 {item.name} | {status} | {display_perim} | [👁️]({u_path}) | [💾]({raw_url}/{u_path}) |")
            else:
                md.append(f"| {indent}📂 **{item.name}** | - | - | - | - |")
        
        # Ajout du retour à la ligne supplémentaire après le tableau
        md.append("\n[⬆️ Retour au sommaire](#-sommaire)\n\n---")

    # 5. Sauvegarde
    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    Path(SETTINGS_FILE).write_text(json.dumps(new_data, indent=4, ensure_ascii=False), encoding="utf-8")
    print("✅ BOM généré avec succès.")

if __name__ == "__main__":
    generate_bom()
