import os
import json
from pathlib import Path
import urllib.parse

def generate_bom():
    # --- CONFIGURATION ---
    root_dir = Path(".")
    output_file = "bom.md"
    settings_file = "print_settings.json"
    exclude = {'.git', '.github', '__pycache__', 'venv', '.vscode'}

    # 1. Chargement/Initialisation du dictionnaire de paramètres
    if Path(settings_file).exists():
        with open(settings_file, "r", encoding="utf-8") as f:
            print_settings = json.load(f)
    else:
        print_settings = {}

    # Définition des valeurs par défaut (SANS support ni layer_height)
    default_settings = {
        "perimeters": "3",
        "top_solid_layers": "4",
        "bottom_solid_layers": "3",
        "fill_density": "15%",
        "fill_pattern": "Grid",
        "infill_anchor": "600%",
        "infill_anchor_max": "50"
    }

    # 2. Analyse des dossiers (niveau 1, ex: MTL)
    level1_dirs = [d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude]

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ Bill of Materials (BOM)\n\n")

        for l1 in level1_dirs:
            # Niveau 2 (ex: Aile, Fuselage)
            level2_dirs = sorted([d for d in l1.iterdir() if d.is_dir()])
            
            for module in level2_dirs:
                stls = sorted(list(module.rglob("*.stl")))
                if not stls: continue

                f.write(f"## 📦 Module : {module.name.replace('_', ' ')}\n")
                f.write(f"Section : `{l1.name}`\n\n")
                
                # En-têtes textuels clairs
                f.write("| Structure | Périmètres | Couches | Densité | Pattern | Ancre / Max | Vue 3D | Download |\n")
                f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")

                for item in sorted(list(module.rglob("*"))):
                    if item.is_dir() or item.suffix.lower() == ".stl":
                        rel_path = str(item.relative_to(root_dir))
                        depth = len(item.relative_to(module).parts)
                        
                        # Hiérarchie avec slashs
                        indent = "&nbsp;" * 4 * depth + "/ " if depth > 0 else ""
                        icon = "📂" if item.is_dir() else "📄"
                        
                        per, tb, dens, pat, anc, view, dl = ["-"] * 7
                        
                        if item.suffix.lower() == ".stl":
                            # Fusion intelligente pour ne garder que les clés voulues
                            current = print_settings.get(rel_path, {})
                            # On ne garde que les clés présentes dans default_settings
                            settings = {k: current.get(k, v) for k, v in default_settings.items()}
                            print_settings[rel_path] = settings
                            
                            per = settings['perimeters']
                            tb = f"🔝{settings['top_solid_layers']} / ⬇️{settings['bottom_solid_layers']}"
                            dens = settings['fill_density']
                            pat = settings['fill_pattern']
                            anc = f"{settings['infill_anchor']} / {settings['infill_anchor_max']}"
                            
                            url_path = urllib.parse.quote(rel_path)
                            view = f"[👁️]({url_path})"
                            dl = f"[💾]({url_path}?raw=true)"

                        name = f"**{item.name}**" if item.is_dir() else item.name
                        f.write(f"| {indent}{icon} {name} | {per} | {tb} | {dens} | {pat} | {anc} | {view} | {dl} |\n")
                
                f.write("\n---\n\n")

    # Sauvegarde du JSON "propre"
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(print_settings, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    generate_bom()
