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
        # Vérifie d'abord si on est dans un dépôt git
        if not Path(".git").exists():
            return ".", "."
            
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], 
                                       text=True, stderr=subprocess.DEVNULL).strip()
        
        # Nettoyage de l'URL pour gérer HTTPS et SSH
        repo = url.replace("https://github.com", "").replace("git@github.com:", "").removesuffix(".git")
        # S'assurer qu'il n'y a pas de slash résiduel au début
        repo = repo.lstrip("/")
        
        return f"https://raw.githubusercontent.com{repo}/main", f"https://github.com{repo}/blob/main"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ".", "."

def check(v):
    return f"**{v}**" if v and str(v).strip() else "🔴 _À définir_"

def generate_bom():
    root = Path(".")
    arc_dir = root / "archives"

    # Nettoyage et création sécurisée du dossier archives
    if arc_dir.exists():
        shutil.rmtree(arc_dir)
    arc_dir.mkdir(parents=True, exist_ok=True)

    raw_url, blob_url = get_repo_info()

    # Chargement des données
    existing_data = {}
    if Path(SETTINGS_FILE).exists():
        try:
            existing_data = json.loads(Path(SETTINGS_FILE).read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"⚠️ Attention : {SETTINGS_FILE} est corrompu. Création d'un nouveau fichier.")

    existing_common = existing_data.get("COMMON_SETTINGS", {})
    new_data = {"COMMON_SETTINGS": {k: existing_common.get(k) for k in COMMON_KEYS}}

    # Scan des modules : On ignore explicitement 'archives' et les dossiers dans EXCLUDE
    sections = []
    # Liste les dossiers parents (ex: 'Parties_Mecaniques')
    for l1 in sorted(d for d in root.iterdir() if d.is_dir() and d.name not in EXCLUDE):
        # Liste les modules (ex: 'Axe_X')
        for m in sorted(d for d in l1.iterdir() if d.is_dir()):
            if any(m.rglob("*.stl")):
                sections.append((m, l1.name))

    # --- Génération du Markdown ---
    md = ["# 📋 Nomenclature (BOM)\n", "## 📌 Sommaire"]
    for m, _ in sections:
        anchor = m.name.lower().replace('_', '-').replace(' ', '-')
        md.append(f"- [{m.name.replace('_', ' ').capitalize()}](#-{anchor})")

    # Paramètres communs
    c = new_data["COMMON_SETTINGS"]
    md += [
        "\n---\n", "## ⚙️ Paramètres d'Impression\n",
        "| Paramètre | Valeur |", 
        "| :--- | :--- |",
        f"| Couches (H/B) | {check(c.get('top_solid_layers'))} / {check(c.get('bottom_solid_layers'))} |",
        f"| Remplissage | {check(c.get('fill_density'))} ({check(c.get('fill_pattern'))}) |",
        "\n---"
    ]

    for mod, parent in sections:
        safe_name = mod.name.replace(" ", "_")
        # On place l'archive dans le dossier archives
        zip_base_path = arc_dir / safe_name
        shutil.make_archive(str(zip_base_path), 'zip', root_dir=mod)
        zip_url = f"{raw_url}/archives/{urllib.parse.quote(safe_name)}.zip"

        md += [
            f"\n## 📦 {mod.name.replace('_', ' ').capitalize()}",
            f"Section : `{parent}` | **[🗜️ Télécharger le module complet (ZIP)]({zip_url})**\n",
            "| Vue 3D | Structure | État | Périmètres | Télécharger |",
            "| :---: | :--- | :---: | :---: | :---: |"
        ]

        # Utilisation de rglob pour trouver tous les fichiers et dossiers
        for item in sorted(mod.rglob("*")):
            # On ignore les fichiers non STL mais on garde les dossiers pour l'arborescence
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
                    f"| [🔍]({blob_url}/{u_path}) "
                    f"| {indent}📄 {item.name} "
                    f"| {'🟢' if old_val else '🔴'} "
                    f"| {old_val if old_val else '---'} "
                    f"| [💾]({raw_url}/{u_path}) |"
                )
            else:
                md.append(f"| | {indent}📂 **{item.name}** | - | - | - |")

        md.append("\n[⬆️ Sommaire](#-sommaire)\n\n---")

    # Sortie finale
    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    # Utilisation du module [json](https://docs.python.org) pour persister les réglages
    Path(SETTINGS_FILE).write_text(json.dumps(new_data, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"✅ BOM généré avec succès dans {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_bom()
