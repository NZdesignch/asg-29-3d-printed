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
    """Récupère dynamiquement les URLs GitHub ou fallback sur local."""
    try:
        cmd = ["git", "config", "--get", "remote.origin.url"]
        url = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        
        # Nettoyage robuste pour HTTPS et SSH
        repo = url.replace("https://github.com", "").replace("git@github.com:", "").removesuffix(".git")
        repo = repo.strip("/")
        
        return f"https://raw.githubusercontent.com{repo}/main", f"https://github.com{repo}/blob/main"
    except Exception:
        return ".", "."

def check_val(v, default="🔴 _À définir_"):
    """Formate une valeur ou renvoie un indicateur d'absence."""
    return f"**{v}**" if v and str(v).strip() else default

def load_settings():
    """Charge les paramètres existants ou initialise un dictionnaire vide."""
    p = Path(SETTINGS_FILE)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"⚠️ Erreur de lecture de {SETTINGS_FILE}, réinitialisation.")
    return {}

def generate_bom():
    root = Path(".")
    arc_dir = root / "archives"
    
    # Nettoyage propre de l'archive
    if arc_dir.exists():
        shutil.rmtree(arc_dir)
    arc_dir.mkdir(parents=True, exist_ok=True)

    raw_url, blob_url = get_repo_info()
    existing_data = load_settings()
    
    # Initialisation des nouvelles données (conserve les COMMON_SETTINGS existants)
    common_src = existing_data.get("COMMON_SETTINGS", {})
    new_data = {"COMMON_SETTINGS": {k: common_src.get(k) for k in COMMON_KEYS}}

    # Scan des modules (plus lisible avec des list comprehensions)
    sections = []
    for l1 in sorted(d for d in root.iterdir() if d.is_dir() and d.name not in EXCLUDE):
        for m in sorted(d for d in l1.iterdir() if d.is_dir()):
            if any(m.rglob("*.stl")):
                sections.append((m, l1.name))

    # --- Construction du Markdown ---
    md = ["# 📋 Nomenclature (BOM)\n", "## 📌 Sommaire"]
    
    # Sommaire dynamique
    for m, _ in sections:
        anchor = m.name.lower().replace("_", "-").replace(" ", "-")
        title = m.name.replace('_', ' ').capitalize()
        md.append(f"- [{title}](#{anchor})")

    # Table des paramètres globaux
    c = new_data["COMMON_SETTINGS"]
    md += [
        "\n---\n", "## ⚙️ Paramètres d'Impression\n",
        "| Paramètre | Valeur |",
        "| :--- | :--- |",
        f"| Couches Solides | {check_val(c.get('top_solid_layers'))} (H) / {check_val(c.get('bottom_solid_layers'))} (B) |",
        f"| Remplissage | {check_val(c.get('fill_density'))} ({check_val(c.get('fill_pattern'))}) |",
        "\n---"
    ]

    for mod, parent in sections:
        display_name = mod.name.replace('_', ' ').capitalize()
        safe_name = mod.name.replace(" ", "_")
        
        # Création ZIP (on ignore le dossier archives lui-même s'il est dedans)
        shutil.make_archive(str(arc_dir / safe_name), 'zip', root_dir=mod)
        zip_url = f"{raw_url}/archives/{urllib.parse.quote(safe_name + '.zip')}"

        md += [
            f"\n## 📦 {display_name}",
            f"**Dossier parent :** `{parent}` | **[📥 Télécharger tout le module (ZIP)]({zip_url})**\n",
            "| Fichier | État | Périmètres | Actions |",
            "| :--- | :---: | :---: | :---: |"
        ]

        # Parcours récursif des fichiers STL uniquement pour la table
        for item in sorted(mod.rglob("*")):
            if item.is_dir() or item.suffix.lower() != ".stl":
                continue
            
            rel_path = item.relative_to(root)
            u_path = urllib.parse.quote(rel_path.as_posix(), safe='/')
            
            # Récupération/Conservation de la donnée "perimeters"
            old_perim = existing_data.get(str(rel_path), {}).get("perimeters")
            new_data[str(rel_path)] = {"perimeters": old_perim}
            
            status_icon = "🟢" if old_perim else "🔴"
            
            md.append(
                f"| 📄 {item.name} "
                f"| {status_icon} "
                f"| {old_perim or '---'} "
                f"| [🔍 Voir]({blob_url}/{u_path}) - [💾 RAW]({raw_url}/{u_path}) |"
            )

        md.append("\n[⬆️ Retour au sommaire](#-sommaire)\n\n---")

    # Écriture des fichiers
    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    Path(SETTINGS_FILE).write_text(json.dumps(new_data, indent=4, ensure_ascii=False), encoding="utf-8")
    
    print(f"✅ Terminé ! {len(sections)} modules traités.")

if __name__ == "__main__":
    generate_bom()
