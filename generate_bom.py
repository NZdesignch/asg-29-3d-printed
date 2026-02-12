import json
import shutil
import subprocess
import urllib.parse
from pathlib import Path
from contextlib import suppress

# --- CONSTANTES ---
EXCLUDE = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives'}
COMMON_KEYS = [
    "top_solid_layers", "bottom_solid_layers", 
    "fill_density", "fill_pattern", 
    "infill_anchor", "infill_anchor_max"
]

def get_raw_url():
    """Récupère l'URL de base GitHub Raw avec une gestion d'erreur simplifiée."""
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        path = url.split("github.com")[-1].replace(".git", "").replace(":", "/")
        return f"https://raw.githubusercontent.com{path}/main"
    except Exception:
        return "."

def format_name(name):
    """Formate les noms de fichiers/dossiers pour le Markdown."""
    return name.replace('_', ' ').strip().capitalize()

def check_val(val):
    """Retourne la valeur formatée ou une alerte si vide."""
    return f"**{val}**" if val and str(val).strip() else "🔴 _À définir_"

def generate_bom():
    root = Path(".")
    archive_dir = root / "archives"
    archive_dir.mkdir(exist_ok=True)
    
    settings_path = root / "print_settings.json"
    raw_url = get_raw_url()
    
    # 1. Chargement sécurisé des réglages existants
    existing_data = {}
    if settings_path.exists():
        with suppress(json.JSONDecodeError):
            existing_data = json.loads(settings_path.read_text(encoding="utf-8"))

    # 2. Préparation du nouveau dictionnaire de données
    new_data = {"COMMON_SETTINGS": {k: existing_data.get("COMMON_SETTINGS", {}).get(k) for k in COMMON_KEYS}}
    
    # 3. Analyse de la structure (un seul passage)
    sections = {}
    for l1 in sorted(root.iterdir()):
        if l1.is_dir() and l1.name not in EXCLUDE:
            for m in sorted(l1.iterdir()):
                if m.is_dir() and any(m.glob("*.stl")):
                    sections.setdefault(l1.name, []).append(m)

    # 4. Construction du contenu Markdown
    md = ["# 🛠️ Nomenclature (BOM)\n", "## 📌 Sommaire"]
    
    # Sommaire
    for modules in sections.values():
        for mod in modules:
            md.append(f"- [{format_name(mod.name)}](#-{mod.name.lower().replace('_', '-')})")
    
    # Paramètres globaux
    common = new_data["COMMON_SETTINGS"]
    md.extend([
        "\n---\n\n## ⚙️ Paramètres d'Impression Généraux\n",
        "| Paramètre | Valeur |", "| :--- | :--- |",
        f"| Couches Solides | {check_val(common['top_solid_layers'])} / {check_val(common['bottom_solid_layers'])} |",
        f"| Remplissage | {check_val(common['fill_density'])} / {check_val(common['fill_pattern'])} |",
        f"| Ancre de remplissage | {check_val(common['infill_anchor'])} / {check_val(common['infill_anchor_max'])} |\n\n---"
    ])

    # Sections par module
    for parent_name, modules in sections.items():
        for mod in modules:
            zip_name = f"module_{mod.name.replace(' ', '_')}"
            shutil.make_archive(str(archive_dir / zip_name), 'zip', root_dir=mod)
            
            dl_link = f"{raw_url}/archives/{urllib.parse.quote(zip_name)}.zip"
            md.extend([f"\n## 📦 {format_name(mod.name)}", f"Section : `{parent_name}` | **[🗜️ Télécharger ZIP]({dl_link})**\n"])
            md.append("| Structure | État | Périmètres | Vue 3D | Download |\n| :--- | :---: | :---: | :---: | :---: |")

            for item in sorted(mod.rglob("*")):
                if not (item.is_dir() or item.suffix.lower() == ".stl"): continue
                
                rel = str(item.relative_to(root))
                depth = len(item.relative_to(mod).parts)
                prefix = f"{'&nbsp;' * 4 * depth}/ " if depth > 0 else ""
                
                if item.suffix.lower() == ".stl":
                    val = existing_data.get(rel, {}).get("perimeters")
                    new_data[rel] = {"perimeters": val}
                    
                    status = "🟢" if val is not None else "🔴"
                    u_path = urllib.parse.quote(rel)
                    md.append(f"| {prefix}📄 {item.name} | {status} | {val or '---'} | [👁️]({u_path}) | [💾]({raw_url}/{u_path}) |")
                else:
                    md.append(f"| {prefix}📂 **{item.name}** | - | - | - | - |")
            
            md.append(f"\n[⬆️ Retour au sommaire](#-sommaire)\n\n---")

    # 5. Sauvegarde atomique (Ecriture disque unique)
    (root / "bom.md").write_text("\n".join(md), encoding="utf-8")
    settings_path.write_text(json.dumps(new_data, indent=4, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    generate_bom()
