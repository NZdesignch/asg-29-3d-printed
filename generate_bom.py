import json
import shutil
import subprocess
import urllib.parse
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

def get_repo_info():
    """Récupère proprement les URLs GitHub."""
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], 
                                       text=True, stderr=subprocess.DEVNULL).strip()
        repo = url.replace("https://github.com", "").replace("git@github.com:", "").removesuffix(".git")
        repo = repo.lstrip("/")
        return f"https://raw.githubusercontent.com{repo}/main", f"https://github.com{repo}/blob/main"
    except:
        return ".", "."

def check(v):
    """Formatage visuel des valeurs."""
    return f"**{v}**" if v and str(v).strip() else "🔴 _À définir_"

def generate_anchor(name):
    """Génère une ancre compatible avec le moteur Markdown de GitHub."""
    # GitHub ignore l'émoji du titre et ne garde que le texte pour l'ID
    anchor = name.lower().replace(" ", "-").replace("_", "-")
    # On retire les caractères spéciaux courants pour être sûr
    return anchor

def generate_bom():
    root = Path(".")
    arc_dir = root / "archives"

    # Nettoyage du dossier archives
    if arc_dir.exists():
        shutil.rmtree(arc_dir)
    arc_dir.mkdir(parents=True, exist_ok=True)

    raw_url, blob_url = get_repo_info()

    # Chargement des données existantes
    existing_data = {}
    if Path(SETTINGS_FILE).exists():
        try:
            existing_data = json.loads(Path(SETTINGS_FILE).read_text(encoding="utf-8"))
        except:
            pass

    existing_common = existing_data.get("COMMON_SETTINGS", {})
    new_data = {"COMMON_SETTINGS": {k: existing_common.get(k) for k in COMMON_KEYS}}

    # Scan des modules
    sections = []
    for l1 in sorted(d for d in root.iterdir() if d.is_dir() and d.name not in EXCLUDE):
        for m in sorted(d for d in l1.iterdir() if d.is_dir()):
            if any(m.rglob("*.stl")):
                sections.append((m, l1.name))

    # --- Construction du Markdown ---
    md = ["# 📋 Nomenclature (BOM)\n", "## 📌 Sommaire"]
    
    for m, _ in sections:
        clean_name = m.name.replace('_', ' ').capitalize()
        # L'ancre doit pointer vers le texte sans l'émoji qui sera dans le titre
        anchor = generate_anchor(m.name)
        md.append(f"- [{clean_name}](#-{anchor})")

    # Paramètres communs
    c = new_data["COMMON_SETTINGS"]
    md += [
        "\n---\n", "## ⚙️ Paramètres d'Impression\n",
        "| Paramètre | Valeur |", "| :--- | :--- |",
        f"| Couches | {check(c.get('top_solid_layers'))} / {check(c.get('bottom_solid_layers'))} |",
        f"| Remplissage | {check(c.get('fill_density'))} / {check(c.get('fill_pattern'))} |",
        "\n---"
    ]

    # Sections détaillées
    for mod, parent in sections:
        display_name = mod.name.replace('_', ' ').capitalize()
        safe_name = mod.name.replace(" ", "_")
        
        # Création du ZIP
        shutil.make_archive(str(arc_dir / safe_name), 'zip', root_dir=mod)
        zip_url = f"{raw_url}/archives/{urllib.parse.quote(safe_name)}.zip"

        # IMPORTANT : Le titre contient l'émoji, mais l'ancre GitHub générée automatiquement 
        # par le navigateur se basera sur le texte.
        md += [
            f"\n## 📦 {display_name}",
            f"Section : `{parent}` | **[🗜️ ZIP]({zip_url})**\n",
            "| Vue 3D | Structure | État | Périmètres | Télécharger |",
            "| :---: | :--- | :---: | :---: | :---: |"
        ]

        for item in sorted(mod.rglob("*")):
            if item.is_file() and item.suffix.lower() != ".stl":
                continue

            rel_path = item.relative_to(root)
            depth = len(item.relative_to(mod).parts)
            indent = "&nbsp;" * 4 * depth + ("┕ " if depth > 0 else "")

            if item.is_file():
                u_path = urllib.parse.quote(rel_path.as_posix())
                old_val = existing_data.get(str(rel_path), {}).get("perimeters")
                new_data[str(rel_path)] = {"perimeters": old_val}
                
                md.append(
                    f"| [🔍 Voir]({blob_url}/{u_path}) "
                    f"| {indent}📄 {item.name} "
                    f"| {'🟢' if old_val else '🔴'} "
                    f"| {old_val or '---'} "
                    f"| [💾]({raw_url}/{u_path}) |"
                )
            else:
                md.append(f"| | {indent}📂 **{item.name}** | - | - | - |")

        md.append("\n[⬆️ Retour au Sommaire](#-sommaire)\n\n---")

    # Écriture des fichiers
    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    Path(SETTINGS_FILE).write_text(json.dumps(new_data, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"✅ BOM généré avec succès.")

if __name__ == "__main__":
    generate_bom()
