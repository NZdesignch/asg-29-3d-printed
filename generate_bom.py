import os
import json
import shutil
import subprocess
from pathlib import Path
import urllib.parse

def get_github_repo_info():
    """Récupère l'URL raw de GitHub."""
    try:
        remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"]).decode().strip()
        repo_path = remote_url.replace("https://github.com", "").replace(".git", "").replace("git@github.com:", "")
        return f"https://raw.githubusercontent.com{repo_path}/main"
    except Exception:
        return "."

def generate_bom():
    root_dir = Path(".")
    output_file = "bom.md"
    settings_file = "print_settings.json"
    archive_dir = Path("archives")
    exclude = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives'}
    
    archive_dir.mkdir(exist_ok=True)
    base_raw_url = get_github_repo_info()

    # --- 1. CHARGEMENT ET PROTECTION DES DONNÉES ---
    existing_data = {}
    if Path(settings_file).exists():
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    existing_data = json.loads(content)
        except json.JSONDecodeError as e:
            # SÉCURITÉ : Si le JSON est corrompu, on arrête tout pour ne rien écraser
            print(f"❌ ERREUR SYNTAXE JSON (Ligne {e.lineno}) : Le script s'arrête pour protéger vos données.")
            return 

    # --- 2. FUSION DES PARAMÈTRES COMMUNS ---
    common_keys = ["top_solid_layers", "bottom_solid_layers", "fill_density", "fill_pattern", "infill_anchor", "infill_anchor_max"]
    old_common = existing_data.get("COMMON_SETTINGS", {})
    
    # On garde la valeur existante, sinon on met None
    new_data = {
        "COMMON_SETTINGS": {k: old_common.get(k) for k in common_keys}
    }
    common = new_data["COMMON_SETTINGS"]

    # --- 3. ANALYSE ET GÉNÉRATION ---
    level1_dirs = sorted([d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude])
    modules_list = []
    for l1 in level1_dirs:
        l2_dirs = sorted([d for d in l1.iterdir() if d.is_dir()])
        for m in l2_dirs:
            if list(m.rglob("*.stl")):
                modules_list.append((m, l1.name))

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ Nomenclature (BOM)\n\n")

        # Sommaire
        f.write("## 📌 Sommaire\n")
        for mod_path, _ in modules_list:
            anchor = mod_path.name.lower().replace(" ", "-").replace("_", "-")
            f.write(f"- [Module : {mod_path.name.replace('_', ' ')}](#-module--{anchor})\n")
        f.write("\n---\n\n")

        # Paramètres Communs
        f.write("## ⚙️ Paramètres d'Impression Généraux\n\n")
        def check(val): return val if val is not None else "🔴 _À définir_"
        f.write("| Paramètre | Valeur |\n| :--- | :--- |\n")
        f.write(f"| Couches Solides (Dessus / Dessous) | {check(common['top_solid_layers'])} / {check(common['bottom_solid_layers'])} |\n")
        f.write(f"| Remplissage (Densité / Motif) | {check(common['fill_density'])} / {check(common['fill_pattern'])} |\n")
        f.write(f"| Ancre de remplissage (Valeur / Max) | {check(common['infill_anchor'])} / {check(common['infill_anchor_max'])} |\n\n")
        f.write("---\n\n")

        for module_path, parent_name in modules_list:
            # Gestion ZIP
            safe_name = module_path.name.replace(" ", "_")
            zip_filename = f"module_{safe_name}"
            shutil.make_archive(str(archive_dir / zip_filename), 'zip', root_dir=module_path)
            zip_url = f"{base_raw_url}/archives/{urllib.parse.quote(zip_filename + '.zip')}"

            f.write(f"## 📦 Module : {module_path.name.replace('_', ' ')}\n")
            f.write(f"Section : `{parent_name}` | **[🗜️ Télécharger ZIP]({zip_url})**\n\n")
            f.write("| Structure | État | Périmètres | Vue 3D | Download |\n| :--- | :---: | :---: | :---: | :---: |\n")

            for item in sorted(list(module_path.rglob("*"))):
                if item.is_dir() or item.suffix.lower() == ".stl":
                    rel_path = str(item.relative_to(root_dir))
                    depth = len(item.relative_to(module_path).parts)
                    indent = "&nbsp;" * 4 * depth + "/ " if depth > 0 else ""
                    
                    if item.suffix.lower() == ".stl":
                        # --- FUSION DES PÉRIMÈTRES (PROTECTION) ---
                        # On récupère la valeur actuelle. Si elle n'est pas None, elle est conservée.
                        old_perim = existing_data.get(rel_path, {}).get("perimeters")
                        new_data[rel_path] = {"perimeters": old_perim}
                        
                        status = "🟢" if old_perim is not None else "🔴"
                        per = old_perim if old_perim is not None else "---"
                        url_path = urllib.parse.quote(rel_path)
                        view = f"[👁️]({url_path})"
                        dl = f"[💾]({base_raw_url}/{url_path})"

                        f.write(f"| {indent}📄 {item.name} | {status} | {per} | {view} | {dl} |\n")
                    else:
                        f.write(f"| {indent}📂 **{item.name}** | - | - | - | - |\n")
            f.write("\n[⬆️ Retour au sommaire](#-sommaire)\n\n---\n\n")

    # --- 4. SAUVEGARDE FINALE SÉCURISÉE ---
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    generate_bom()
