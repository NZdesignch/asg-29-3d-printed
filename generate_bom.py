import json
import shutil
import subprocess
import urllib.parse
from pathlib import Path

# --- CONFIGURATION ---
OUTPUT_FILE = "bom.md"
SETTINGS_FILE = "print_settings.json"
EXCLUDE = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives', 'previews'}
COMMON_KEYS = ["top_solid_layers", "bottom_solid_layers", "fill_density", "fill_pattern"]

def get_repo_info():
    """Récupère les URLs GitHub (Raw et Blob)."""
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], 
                                       text=True, stderr=subprocess.DEVNULL).strip()
        repo = url.replace("https://github.com", "").replace("git@github.com:", "").removesuffix(".git").strip("/")
        return f"https://raw.githubusercontent.com{repo}/main", f"https://github.com{repo}/blob/main"
    except:
        return ".", "."

def check_val(v):
    return f"**{v}**" if v and str(v).strip() else "🔴 _À définir_"

def generate_bom():
    root = Path(".")
    arc_dir = root / "archives"
    if arc_dir.exists(): shutil.rmtree(arc_dir)
    arc_dir.mkdir(parents=True, exist_ok=True)

    raw_url, blob_url = get_repo_info()

    # Chargement des réglages existants
    existing_data = {}
    if Path(SETTINGS_FILE).exists():
        try:
            existing_data = json.loads(Path(SETTINGS_FILE).read_text(encoding="utf-8"))
        except: pass

    new_data = {"COMMON_SETTINGS": {k: existing_data.get("COMMON_SETTINGS", {}).get(k) for k in COMMON_KEYS}}

    # Identification des modules (Lvl 2 : Dossier_Parent/Nom_Module)
    sections = []
    for l1 in sorted(d for d in root.iterdir() if d.is_dir() and d.name not in EXCLUDE):
        for m in sorted(d for d in l1.iterdir() if d.is_dir()):
            if any(m.rglob("*.stl")):
                sections.append((m, l1.name))

    md = ["# 📋 Nomenclature (BOM)\n", "## 📌 Sommaire"]
    for m, _ in sections:
        anchor = m.name.lower().replace("_", "-").replace(" ", "-")
        md.append(f"- [{m.name.replace('_', ' ').capitalize()}](#{anchor})")

    # Table des paramètres globaux
    c = new_data["COMMON_SETTINGS"]
    md += ["\n---\n", "## ⚙️ Paramètres d'Impression\n", "| Paramètre | Valeur |", "| :--- | :--- |",
           f"| Couches | {check_val(c.get('top_solid_layers'))} / {check_val(c.get('bottom_solid_layers'))} |",
           f"| Remplissage | {check_val(c.get('fill_density'))} / {check_val(c.get('fill_pattern'))} |", "\n---"]

    for mod, parent in sections:
        display_name = mod.name.replace('_', ' ').capitalize()
        safe_zip = mod.name.replace(" ", "_")
        
        # Archivage du module complet
        shutil.make_archive(str(arc_dir / safe_zip), 'zip', root_dir=mod)
        zip_link = f"{raw_url}/archives/{urllib.parse.quote(safe_zip + '.zip')}"

        md += [f"\n## 📦 {display_name}",
               f"Section : `{parent}` | **[🗜️ ZIP complet]({zip_link})**\n",
               "| Fichier / Structure | État | Périmètres | Actions |",
               "| :--- | :---: | :---: | :---: |"]

        # Parcours de TOUS les éléments du module pour reconstruire l'arborescence
        # On trie pour garantir que les dossiers apparaissent avant leurs fichiers
        for item in sorted(mod.rglob("*")):
            # On ignore les fichiers non STL (sauf les dossiers pour la structure)
            if item.is_file() and item.suffix.lower() != ".stl":
                continue
            
            # Calcul de l'indentation (profondeur relative au dossier du module)
            depth = len(item.relative_to(mod).parts)
            indent = "&nbsp;" * 6 * (depth - 1) + ("┕ " if depth > 1 else "")
            
            rel_path = item.relative_to(root)
            u_path = urllib.parse.quote(rel_path.as_posix(), safe='/')

            if item.is_dir():
                # On n'affiche le dossier que s'il contient des fichiers STL quelque part
                if any(item.rglob("*.stl")):
                    md.append(f"| {indent}📂 **{item.name}** | - | - | - |")
            else:
                # C'est un fichier STL
                old_val = existing_data.get(str(rel_path), {}).get("perimeters")
                new_data[str(rel_path)] = {"perimeters": old_val}
                
                # Liens compacts pour gagner de la place dans la hiérarchie
                actions = f"[🔍 Voir]({blob_url}/{u_path}) / [💾 RAW]({raw_url}/{u_path})"
                
                md.append(f"| {indent}📄 {item.name} "
                          f"| {'🟢' if old_val else '🔴'} "
                          f"| {old_val or '---'} "
                          f"| {actions} |")

        md.append("\n[⬆️ Sommaire](#-sommaire)\n\n---")

    # Sauvegarde
    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    Path(SETTINGS_FILE).write_text(json.dumps(new_data, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"✅ BOM généré avec structure hiérarchique.")

if __name__ == "__main__":
    generate_bom()
