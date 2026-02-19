import json, shutil, subprocess, urllib.parse, pyvista as pv
from pathlib import Path

# --- CONFIGURATION ---
OUTPUT_FILE, SETTINGS_FILE = "bom.md", "print_settings.json"
EXCLUDE = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives', 'previews'}
COMMON_KEYS = ["top_solid_layers", "bottom_solid_layers", "fill_density", "fill_pattern", "infill_anchor", "infill_anchor_max"]

def get_raw_url():
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        repo = url.replace("https://github.com", "").replace("git@github.com:", "").removesuffix(".git")
        return f"https://raw.githubusercontent.com{repo}/main"
    except: return "."

def generate_preview(stl_path, img_path):
    """Génère une image PNG grise sur fond blanc pour le STL."""
    try:
        mesh = pv.read(str(stl_path))
        plotter = pv.Plotter(off_screen=True)
        plotter.add_mesh(mesh, color="#7fb3d5") # Un joli bleu-gris propre
        plotter.view_isometric()
        plotter.background_color = "white"
        plotter.screenshot(str(img_path))
        plotter.close()
    except Exception as e:
        print(f"⚠️ Erreur de rendu pour {stl_path.name}: {e}")

def generate_bom():
    root, arc_dir, prev_dir = Path("."), Path("archives"), Path("previews")
    
    # Nettoyage et création des dossiers
    for d in [arc_dir, prev_dir]:
        if d.exists(): shutil.rmtree(d)
        d.mkdir(exist_ok=True)
    
    existing_data = json.loads(Path(SETTINGS_FILE).read_text("utf-8")) if Path(SETTINGS_FILE).exists() else {}
    new_data = {"COMMON_SETTINGS": {k: existing_data.get("COMMON_SETTINGS", {}).get(k) for k in COMMON_KEYS}}
    raw_url = get_raw_url()
    
    sections = [(m, l1.name) for l1 in sorted(root.iterdir()) if l1.is_dir() and l1.name not in EXCLUDE 
                for m in sorted(l1.iterdir()) if m.is_dir() and any(m.rglob("*.stl"))]

    md = ["# 📋 Nomenclature (BOM)\n", "## 📌 Sommaire"]
    md += [f"- [{m.name.replace('_', ' ').capitalize()}](#-{m.name.lower().replace('_', '-')})" for m, _ in sections]
    
    # Paramètres d'impression généraux
    c = new_data["COMMON_SETTINGS"]
    md += ["\n---\n", "## ⚙️ Paramètres Généraux\n", "| Paramètre | Valeur |", "| :--- | :--- |",
           f"| Couches Solides | {c.get('top_solid_layers') or '---'} / {c.get('bottom_solid_layers') or '---'} |",
           f"| Remplissage | {c.get('fill_density') or '---'} / {c.get('fill_pattern') or '---'} |\n", "---"]

    for mod, parent in sections:
        shutil.make_archive(str(arc_dir / mod.name), 'zip', root_dir=mod)
        md += [f"\n## 📦 {mod.name.replace('_', ' ').capitalize()}", 
               f"Section : `{parent}` | **[🗜️ ZIP]({raw_url}/archives/{urllib.parse.quote(mod.name)}.zip)**\n",
               "| Aperçu | Fichier | État | Périm. | 3D | 💾 |", "| :---: | :--- | :---: | :---: | :---: | :---: |"]

        for item in sorted(mod.rglob("*.stl")):
            rel_p = item.relative_to(root)
            # On génère l'image 3D
            img_name = f"{item.stem}.png"
            img_path = prev_dir / img_name
            generate_preview(item, img_path)
            
            old_val = existing_data.get(str(rel_p), {}).get("perimeters")
            new_data[str(rel_p)] = {"perimeters": old_val}
            u_path, u_img = urllib.parse.quote(str(rel_p)), urllib.parse.quote(img_name)
            
            md.append(f"| ![]({raw_url}/previews/{u_img}) | 📄 {item.name} | {'🟢' if old_val else '🔴'} | {old_val or '---'} | [👁️]({u_path}) | [💾]({raw_url}/{u_path}) |")
        
        md.append("\n[⬆️ Retour au sommaire](#-sommaire)\n\n---")

    Path(OUTPUT_FILE).write_text("\n".join(md), "utf-8")
    Path(SETTINGS_FILE).write_text(json.dumps(new_data, indent=4, ensure_ascii=False), "utf-8")
    print(f"✅ BOM et Previews 3D générés.")

if __name__ == "__main__":
    generate_bom()
