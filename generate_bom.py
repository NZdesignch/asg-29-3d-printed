import os
import json
from pathlib import Path
import urllib.parse

def vertical(text):
    """Transforme un texte en vertical pour le Markdown en insérant des <br>."""
    return "<br>".join(list(text))

def generate_bom():
    root_dir = Path(".")
    output_file = "bom.md"
    settings_file = "print_settings.json"
    exclude = {'.git', '.github', '__pycache__', 'venv', '.vscode'}

    if Path(settings_file).exists():
        with open(settings_file, "r", encoding="utf-8") as f:
            print_settings = json.load(f)
    else:
        print_settings = {}

    default_settings = {
        "perimeters": None,
        "top_solid_layers": None,
        "bottom_solid_layers": None,
        "fill_density": None,
        "fill_pattern": None,
        "infill_anchor": None,
        "infill_anchor_max": None
    }

    level1_dirs = [d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude]

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ Bill of Materials (BOM)\n\n")
        f.write("> **Statut :** 🟢 Complété | 🔴 À renseigner dans `print_settings.json`\n\n")

        # --- PRÉPARATION DES EN-TÊTES VERTICAUX ---
        h_etat = vertical("État")
        h_peri = vertical("Périmètres")
        h_couc = vertical("Couches")
        h_dens = vertical("Densité")
        h_patt = vertical("Pattern")
        h_ancr = vertical("Ancre(Max)")
        h_vue  = vertical("Vue3D")
        h_down = vertical("Download")

        for l1 in level1_dirs:
            level2_dirs = sorted([d for d in l1.iterdir() if d.is_dir()])
            
            for module in level2_dirs:
                stls = sorted(list(module.rglob("*.stl")))
                if not stls: continue

                f.write(f"## 📦 Module : {module.name.replace('_', ' ')}\n")
                f.write(f"Section : `{l1.name}`\n\n")
                
                # Tableau avec en-têtes verticaux
                f.write(f"| Structure | {h_etat} | {h_peri} | {h_couc} | {h_dens} | {h_patt} | {h_ancr} | {h_vue} | {h_down} |\n")
                f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")

                for item in sorted(list(module.rglob("*"))):
                    if item.is_dir() or item.suffix.lower() == ".stl":
                        rel_path = str(item.relative_to(root_dir))
                        depth = len(item.relative_to(module).parts)
                        
                        indent = "&nbsp;" * 4 * depth + "/ " if depth > 0 else ""
                        icon = "📂" if item.is_dir() else "📄"
                        
                        status, per, tb, dens, pat, anc, view, dl = ["-"] * 8
                        
                        if item.suffix.lower() == ".stl":
                            current = print_settings.get(rel_path, {})
                            settings = {k: current.get(k, v) for k, v in default_settings.items()}
                            print_settings[rel_path] = settings
                            
                            is_complete = all(v is not None and str(v).strip() != "" for v in settings.values())
                            status = "🟢" if is_complete else "🔴"
                            
                            get_v = lambda k: settings[k] if settings[k] is not None else "---"
                            
                            per = get_v('perimeters')
                            tb = f"🔝{get_v('top_solid_layers')}<br>⬇️{get_v('bottom_solid_layers')}"
                            dens = get_v('fill_density')
                            pat = get_v('fill_pattern')
                            anc = f"{get_v('infill_anchor')}<br>({get_v('infill_anchor_max')})"
                            
                            url_path = urllib.parse.quote(rel_path)
                            view = f"[👁️]({url_path})"
                            dl = f"[💾]({url_path}?raw=true)"

                        name = f"**{item.name}**" if item.is_dir() else item.name
                        f.write(f"| {indent}{icon} {name} | {status} | {per} | {tb} | {dens} | {pat} | {anc} | {view} | {dl} |\n")
                
                f.write("\n---\n\n")

    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(print_settings, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    generate_bom()
