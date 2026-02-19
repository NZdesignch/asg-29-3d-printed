import json
import shutil
import subprocess
import urllib.parse
import pyvista as pv
from pathlib import Path

# --- CONFIGURATION ---
OUTPUT_FILE = "bom.md"
SETTINGS_FILE = "print_settings.json"
EXCLUDE = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives', 'previews'}
COMMON_KEYS = [
    "top_solid_layers", "bottom_solid_layers", 
    "fill_density", "fill_pattern", 
    "infill_anchor", "infill_anchor_max"
]

def get_raw_url():
    """Récupère l'URL du dépôt pour les liens GitHub."""
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        repo = url.replace("https://github.com", "").replace("git@github.com:", "").removesuffix(".git")
        return f"https://raw.githubusercontent.com{repo}/main"
    except:
        return "."

def generate_preview(stl_path, img_path):
    """Génère un rendu 3D avec fond transparent."""
    try:
        mesh = pv.read(str(stl_path))
        plotter = pv.Plotter(off_screen=True)
        # Ajout du mesh avec une couleur propre et lissage
        plotter.add_mesh(mesh, color="#7fb3d5", smooth_shading=True) 
        plotter.view_isometric()
        # Activation de la transparence lors de la capture
        plotter.screenshot(str(img_path), transparent_background=True)
        plotter.close()
    except Exception as e:
        print(f"⚠️ Erreur rendu {stl_path.name}: {e}")

def check(v):
    if v is not None and str(v).strip() != "":
        return f"**{v}**"
    return "🔴 _À définir_"

def generate_bom():
    root = Path(".")
    arc_dir, prev_dir = root / "archives", root / "previews"
    
    # --- NETTOYAGE ET PRÉPARATION ---
    for d in [arc_dir, prev_dir]:
        if d.exists(): shutil.rmtree(d)
        d.mkdir(exist_ok=True)
    
    raw_url = get_raw_url()
    
    # 1. Chargement des réglages existants
    existing_data = {}
    if Path(SETTINGS_FILE).exists():
        try:
            existing_data = json.loads(Path(SETTINGS_FILE).read_text(encoding="utf-8"))
        except: pass

    new_data = {"COMMON_SETTINGS": {k: existing_data.get("COMMON_SETTINGS", {}).get(k) for k in COMMON_KEYS}}

    # 2. Analyse de l'arborescence (Niveau 1 > Niveau 2)
    sections = []
    level1_dirs = sorted([d for d in root.iterdir() if d.is_dir() and d.name not in EXCLUDE])
    for l1 in level1_dirs:
        for m in sorted([d for d in l1.iterdir() if d.is_dir()]):
            if any(m.rglob("*.stl")):
                sections.append((m, l1.name))

    # 3. Header & Sommaire
    md = ["# 📋 Nomenclature (BOM)\n", "## 📌 Sommaire"]
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
        # Création de l'archive ZIP
        safe_name = mod.name.replace(" ", "_")
        shutil.make_archive(str(arc_dir / safe_name), 'zip', root_dir=mod)
        zip_url = f"{raw_url}/archives/{urllib.parse.quote(safe_name)}.zip"
        
        md.extend([
            f"\n## 📦 {mod.name.replace('_', ' ').capitalize()}",
            f"Section : `{parent}` | **[🗜️ Télécharger ZIP]({zip_url})**\n",
            "| Aperçu | Structure | État | Périmètres | Vue 3D | Download |",
            "| :---: | :--- | :---: | :---: | :---: | :---: |"
        ])

        # Scan récursif des fichiers
        for item in sorted(mod.rglob("*")):
            if not (item.is_dir() or item.suffix.lower() == ".stl"):
                continue
                
            rel_path = str(item.relative_to(root))
            depth = len(item.relative_to(mod).parts)
            indent = "&nbsp;" * 4 * depth + "/ " if depth > 0 else ""
            
            if item.suffix.lower() == ".stl":
                # Génération Image 3D transparente
                img_name = f"{item.stem}.png"
                img_path = prev_dir / img_name
                generate_preview(item, img_path)
                
                # HTML pour miniature petite (60px)
                u_img = urllib.parse.quote(img_name)
                img_tag = f"<img src='{raw_url}/previews/{u_img}' width='60' style='background: transparent;'>"
                
                old_val = existing_data.get(rel_path, {}).get("perimeters")
                new_data[rel_path] = {"perimeters": old_val}
                
                u_path = urllib.parse.quote(rel_path)
                md.append(f"| {img_tag} | {indent}📄 {item.name} | {'🟢' if old_val else '🔴'} | {old_val or '---'} | [👁️]({u_path}) | [💾]({raw_url}/{u_path}) |")
            else:
                md.append(f"| | {indent}📂 **{item.name}** | - | - | - | - |")
        
        md.append("\n[⬆️ Retour au sommaire](#-sommaire)\n\n---")

    # 5. Sauvegarde
    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    Path(SETTINGS_FILE).write_text(json.dumps(new_data, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"✅ BOM terminé : Images transparentes (60px) et Archives prêtes.")

if __name__ == "__main__":
    generate_bom()
