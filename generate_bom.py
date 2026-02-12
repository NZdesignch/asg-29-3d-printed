import json
import shutil
import subprocess
import urllib.parse
from pathlib import Path
from contextlib import suppress

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
    """Récupère l'URL de base GitHub Raw."""
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        path = url.split("github.com")[-1].replace(".git", "").replace("git@github.com:", "/")
        if not path.startswith("/"): path = "/" + path
        return f"https://raw.githubusercontent.com{path}/main"
    except Exception:
        return "."

def generate_bom():
    root = Path(".")
    archive_dir = root / "archives"
    archive_dir.mkdir(exist_ok=True)
    
    settings_path = root / SETTINGS_FILE
    raw_url = get_raw_url()
    
    # 1. Chargement des données
    existing_data = {}
    if settings_path.exists():
        with suppress(json.JSONDecodeError):
            existing_data = json.loads(settings_path.read_text(encoding="utf-8"))

    new_data = {"COMMON_SETTINGS": {k: existing_data.get("COMMON_SETTINGS", {}).get(k) for k in COMMON_KEYS}}
    
    # 2. Analyse des modules (Niveau 1 / Niveau 2)
    sections = []
    level1_dirs = sorted([d for d in root.iterdir() if d.is_dir() and d.name not in EXCLUDE])
    for l1 in level1_dirs:
        for m in sorted([d for d in l1.iterdir() if d.is_dir()]):
            if any(m.rglob("*.stl")):
                sections.append((m, l1.name))

    # 3. Construction du Markdown
    md = ["# 🛠️ Nomenclature (BOM)\n", "## 📌 Sommaire"]
    
    for mod_path, _ in sections:
        clean_name = mod_path.name.replace('_', ' ').capitalize()
        anchor = mod_path.name.lower().replace(" ", "-").replace("_", "-")
        md.append(f"- [{clean_name}](#-{anchor})")
    
    # Paramètres globaux
    c = new_data["COMMON_SETTINGS"]
    def check(v): return f"**{v}**" if v and str(v).strip() else "🔴 _À définir_"
    
    md.extend([
        "\n---\n", "## ⚙️ Paramètres d'Impression Généraux\n",
        "| Paramètre | Valeur |", "| :--- | :--- |",
        f"| Couches Solides | {check(c['top_solid_layers'])} / {check(c['bottom_solid_layers'])} |",
        f"| Remplissage | {check(c['fill_density'])} / {check(c['fill_pattern'])} |",
        f"| Ancre de remplissage | {check(c['infill_anchor'])} / {check(c['infill_anchor_max'])} |\n",
        "---"
    ])

    # 4. Génération des tableaux par module
    for mod, parent in sections:
        # Création ZIP
        zip_name = f"module_{mod.name.replace(' ', '_')}"
        shutil.make_archive(str(archive_dir / zip_name), 'zip', root_dir=mod)
        
        # Titre et Entête
        clean_title = mod.name.replace('_', ' ').capitalize()
        zip_url = f"{raw_url}/archives/{urllib.parse.quote(zip_name)}.zip"
        
        md.extend([
            f"\n## 📦 {clean_title}",
            f"Section : `{parent}` | **[🗜️ Télécharger ZIP]({zip_url})**\n",
            "| Structure | État | Périmètres | Vue 3D | Download |",
            "| :--- | :---: | :---: | :---: | :---: |"
        ])

        # Parcours des fichiers du module
        for item in sorted(mod.rglob("*")):
            if not (item.is_dir() or item.suffix.lower() == ".stl"):
                continue
                
            rel = str(item.relative_to(root))
            depth = len(item.relative_to(mod).parts)
            indent = "&nbsp;" * 4 * depth + "/ " if depth > 0 else ""
            
            if item.suffix.lower() == ".stl":
                val = existing_data.get(rel, {}).get("perimeters")
                new_data[rel] = {"perimeters": val}
                
                status = "🟢" if val is not None else "🔴"
                u_path = urllib.parse.quote(rel)
                md.append(f"| {indent}📄 {item.name} | {status} | {val if val is not None else '---'} | [👁️]({u_path}) | [💾]({raw_url}/{u_path}) |")
            else:
                md.append(f"| {indent}📂 **{item.name}** | - | - | - | - |")
        
        md.append(f"\n[⬆️ Retour au sommaire](#-sommaire)\n\n---")

    # 5. Sauvegarde (Utilisation des constantes pour éviter l'erreur NameError)
    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    settings_path.write_text(json.dumps(new_data, indent=4, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    generate_bom()
