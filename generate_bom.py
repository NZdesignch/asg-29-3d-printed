import json
import shutil
import subprocess
import urllib.parse
import pyvista as pv
from pathlib import Path

# --- CONFIGURATION ---
OUTPUT_FILE = "bom.md"
SETTINGS_FILE = "print_settings.json"
PREVIEWS_DIR = Path("previews")
EXCLUDE = {'.git', '.github', '__pycache__', 'venv', '.vscode', 'archives', 'previews'}
COMMON_KEYS = [
    "top_solid_layers", "bottom_solid_layers",
    "fill_density", "fill_pattern",
    "infill_anchor", "infill_anchor_max"
]

def get_raw_url():
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        repo = url.replace("https://github.com", "").replace("git@github.com:", "").removesuffix(".git")
        return f"https://raw.githubusercontent.com{repo}/main"
    except:
        return "."

def generate_preview(stl_path, img_path):
    try:
        img_path.parent.mkdir(parents=True, exist_ok=True)
        mesh = pv.read(str(stl_path))

        # Normaliser la taille de la mesh pour un rendu cohérent
        bounds = mesh.bounds
        scale = 1.0 / max(bounds[1]-bounds[0], bounds[3]-bounds[2], bounds[5]-bounds[4])
        mesh = mesh.scale(scale, inplace=False)

        plotter = pv.Plotter(off_screen=True)
        plotter.set_background("white")  # Fond blanc pour mieux voir les détails
        plotter.add_mesh(
            mesh,
            color="#56789a",  # Couleur un peu plus foncée pour le contraste
            smooth_shading=True,
            specular=0.5,      # Ajoute un peu de brillance
            specular_power=10, # Contrôle la netteté des reflets
            ambient=0.3,      # Éclairage ambiant pour adoucir les ombres
        )
        plotter.add_light(pv.Light(position=(3, 3, 3), light_type="scene light"))
        plotter.view_isometric()
        plotter.screenshot(
            str(img_path),
            transparent_background=False,  # Fond blanc pour le contraste
            window_size=[512, 512],        # Taille suffisante
        )
        plotter.close()
    except Exception as e:
        print(f"⚠️ Erreur rendu {stl_path.name}: {e}")

def check(v):
    return f"**{v}**" if v and str(v).strip() != "" else "🔴 _À définir_"

def generate_bom():
    root = Path(".")
    arc_dir = root / "archives"

    # Nettoyage
    for d in [arc_dir, PREVIEWS_DIR]:
        if d.exists(): shutil.rmtree(d)
        d.mkdir(exist_ok=True)

    raw_url = get_raw_url()
    existing_data = {}
    if Path(SETTINGS_FILE).exists():
        try:
            existing_data = json.loads(Path(SETTINGS_FILE).read_text(encoding="utf-8"))
        except:
            pass

    new_data = {"COMMON_SETTINGS": {k: existing_data.get("COMMON_SETTINGS", {}).get(k) for k in COMMON_KEYS}}

    # Génération du sommaire
    sections = []
    level1_dirs = sorted([d for d in root.iterdir() if d.is_dir() and d.name not in EXCLUDE])
    for l1 in level1_dirs:
        for m in sorted([d for d in l1.iterdir() if d.is_dir()]):
            if any(m.rglob("*.stl")):
                sections.append((m, l1.name))

    md = ["# 📋 Nomenclature (BOM)\n", "## 📌 Sommaire"]
    for mod_path, _ in sections:
        clean_name = mod_path.name.replace('_', ' ').capitalize()
        anchor = mod_path.name.lower().replace(" ", "-").replace("_", "-")
        md.append(f"- [{clean_name}](#-{anchor})")

    # Paramètres globaux
    c = new_data["COMMON_SETTINGS"]
    md.extend(["\n---\n", "## ⚙️ Paramètres d'Impression\n", "| Paramètre | Valeur |", "| :--- | :--- |",
               f"| Couches | {check(c.get('top_solid_layers'))} / {check(c.get('bottom_solid_layers'))} |",
               f"| Infill | {check(c.get('fill_density'))} / {check(c.get('fill_pattern'))} |", "---"])

    # Génération des sections
    for mod, parent in sections:
        safe_name = mod.name.replace(" ", "_")
        shutil.make_archive(str(arc_dir / safe_name), 'zip', root_dir=mod)
        zip_url = f"{raw_url}/archives/{urllib.parse.quote(safe_name)}.zip"

        md.extend([f"\n## 📦 {mod.name.replace('_', ' ').capitalize()}",
                   f"Section : `{parent}` | **[🗜️ ZIP]({zip_url})**\n",
                   "| Aperçu | Structure | État | Périmètres | Vue 3D | Download |",
                   "| :---: | :--- | :---: | :---: | :---: | :---: |"])

        for item in sorted(mod.rglob("*")):
            if not (item.is_dir() or item.suffix.lower() == ".stl"): continue

            rel_path = item.relative_to(root)
            depth = len(item.relative_to(mod).parts)
            indent = "&nbsp;" * 4 * depth + "/ " if depth > 0 else ""

            if item.suffix.lower() == ".stl":
                img_path = PREVIEWS_DIR / rel_path.with_suffix(".png")
                generate_preview(item, img_path)
                u_img = urllib.parse.quote(str(img_path.as_posix()))
                img_tag = f"<img src='{raw_url}/{u_img}' width='90' style='background: transparent;'>"
                old_val = existing_data.get(str(rel_path), {}).get("perimeters")
                new_data[str(rel_path)] = {"perimeters": old_val}
                u_path = urllib.parse.quote(str(rel_path.as_posix()))
                md.append(f"| {img_tag} | {indent}📄 {item.name} | {'🟢' if old_val else '🔴'} | {old_val or '---'} | [👁️]({u_path}) | [💾]({raw_url}/{u_path}) |")
            else:
                md.append(f"| | {indent}📂 **{item.name}** | - | - | - | - |")

        md.append("\n[⬆️ Sommaire](#-sommaire)\n\n---")

    # Écriture des fichiers
    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    Path(SETTINGS_FILE).write_text(json.dumps(new_data, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Terminé : Structure 'previews/' miroir créée.")

if __name__ == "__main__":
    generate_bom()
