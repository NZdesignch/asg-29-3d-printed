import json
import re
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
    """
    Récupère les URLs de base du dépôt GitHub via git.
    Retourne (raw_url, blob_url) pour construire les liens vers les fichiers.
    En cas d'échec (pas de dépôt git), retourne (".", ".").
    """
    try:
        url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], text=True).strip()
        repo = url.replace("https://github.com", "").replace("git@github.com:", "").removesuffix(".git")
        return f"https://raw.githubusercontent.com{repo}/main", f"https://github.com{repo}/blob/main"
    except:
        return ".", "."


def check(v):
    """
    Formate une valeur pour l'affichage Markdown :
    - Si la valeur est définie et non vide : retourne la valeur en gras.
    - Sinon : retourne un indicateur visuel "À définir".
    """
    return f"**{v}**" if v and str(v).strip() else "🔴 _À définir_"


def to_github_anchor(heading_text):
    """
    Génère une ancre GitHub valide depuis un texte de titre Markdown.
    Règles GitHub :
    - Tout mettre en minuscules
    - Supprimer les caractères qui ne sont pas des lettres, chiffres, espaces ou tirets
      (cela inclut les emojis et la ponctuation)
    - Remplacer les espaces par des tirets
    """
    anchor = heading_text.lower()
    anchor = re.sub(r'[^\w\s-]', '', anchor)     # supprime emojis et caractères spéciaux
    anchor = re.sub(r'\s+', '-', anchor.strip())  # espaces → tirets
    anchor = re.sub(r'-+', '-', anchor)           # tirets multiples → un seul
    return anchor.strip('-')


def generate_bom():
    """
    Fonction principale : scanne le dépôt, génère le fichier BOM Markdown
    et met à jour le fichier JSON des paramètres d'impression.
    """
    root = Path(".")
    arc_dir = root / "archives"

    # Recrée le dossier d'archives proprement à chaque génération
    if arc_dir.exists():
        shutil.rmtree(arc_dir)
    arc_dir.mkdir()

    raw_url, blob_url = get_repo_info()

    # Charge les données existantes du fichier JSON (pour conserver les valeurs déjà saisies)
    existing_data = {}
    if Path(SETTINGS_FILE).exists():
        try:
            existing_data = json.loads(Path(SETTINGS_FILE).read_text(encoding="utf-8"))
        except:
            pass  # Fichier corrompu ou absent : on repart de zéro

    # Initialise les nouvelles données en récupérant les paramètres communs existants
    existing_common = existing_data.get("COMMON_SETTINGS", {})
    new_data = {"COMMON_SETTINGS": {k: existing_common.get(k) for k in COMMON_KEYS}}

    # Découvre les modules : sous-dossiers de niveau 2 contenant au moins un fichier .stl
    # Structure attendue : <catégorie>/<module>/*.stl
    sections = [
        (m, l1.name)
        for l1 in sorted(d for d in root.iterdir() if d.is_dir() and d.name not in EXCLUDE)
        for m in sorted(d for d in l1.iterdir() if d.is_dir())
        if any(m.rglob("*.stl"))
    ]

    # Pré-calcule les titres pour garantir la cohérence sommaire ↔ sections
    module_headings = {
        m.name: f"📦 {m.name.replace('_', ' ').capitalize()}"
        for m, _ in sections
    }

    # --- Génération du Markdown ---

    # En-tête et sommaire avec liens d'ancrage vers chaque module
    md = ["# 📋 Nomenclature (BOM)\n", "## 📌 Sommaire"]

    # Liens du sommaire : ancre générée depuis le titre réel du heading
    md += [
        f"- [{module_headings[m.name]}](#{to_github_anchor(module_headings[m.name])})"
        for m, _ in sections
    ]

    # Tableau des paramètres d'impression communs
    c = new_data["COMMON_SETTINGS"]
    md += [
        "\n---\n", "## ⚙️ Paramètres d'Impression\n",
        "| Paramètre | Valeur |", "| :--- | :--- |",
        f"| Couches | {check(c.get('top_solid_layers'))} / {check(c.get('bottom_solid_layers'))} |",
        f"| Remplissage | {check(c.get('fill_density'))} / {check(c.get('fill_pattern'))} |",
        "\n---"
    ]

    # Section détaillée pour chaque module
    for mod, parent in sections:
        # Crée une archive ZIP du dossier module pour le téléchargement groupé
        safe_name = mod.name.replace(" ", "_")
        shutil.make_archive(str(arc_dir / safe_name), 'zip', root_dir=mod)
        zip_url = f"{raw_url}/archives/{urllib.parse.quote(safe_name)}.zip"

        # Titre identique à celui utilisé pour générer l'ancre dans le sommaire
        heading = module_headings[mod.name]

        # En-tête de section avec lien ZIP
        md += [
            f"\n## {heading}",
            f"Section : `{parent}` | **[🗜️ ZIP]({zip_url})**\n",
            "| Vue 3D | Structure | État | Périmètres | Télécharger |",
            "| :---: | :--- | :---: | :---: | :---: |"
        ]

        # Parcourt récursivement le module (dossiers et fichiers .stl uniquement)
        for item in sorted(mod.rglob("*")):
            # Ignore les fichiers qui ne sont pas des .stl
            if item.is_file() and item.suffix.lower() != ".stl":
                continue

            rel_path = item.relative_to(root)
            depth = len(item.relative_to(mod).parts)
            # Indentation visuelle en HTML pour refléter la profondeur dans l'arborescence
            indent = "&nbsp;" * 4 * depth + "/ " if depth else ""

            if item.suffix.lower() == ".stl":
                # Encode le chemin pour l'utiliser dans une URL GitHub
                u_path = urllib.parse.quote(rel_path.as_posix())
                # Récupère le nombre de périmètres depuis les données existantes (si défini)
                old_val = existing_data.get(str(rel_path), {}).get("perimeters")
                # Persiste la valeur (même None) dans les nouvelles données
                new_data[str(rel_path)] = {"perimeters": old_val}
                md.append(
                    f"| [🔍 Voir]({blob_url}/{u_path}) "
                    f"| {indent}📄 {item.name} "
                    f"| {'🟢' if old_val else '🔴'} "   # Vert si périmètres définis, rouge sinon
                    f"| {old_val or '---'} "
                    f"| [💾]({raw_url}/{u_path}) |"
                )
            else:
                # Ligne de dossier intermédiaire (sans liens)
                md.append(f"| | {indent}📂 **{item.name}** | - | - | - |")

        # Lien de retour au sommaire en fin de section
        md.append("\n[⬆️ Sommaire](#-sommaire)\n\n---")

    # Écriture des fichiers de sortie
    Path(OUTPUT_FILE).write_text("\n".join(md), encoding="utf-8")
    Path(SETTINGS_FILE).write_text(json.dumps(new_data, indent=4, ensure_ascii=False), encoding="utf-8")
    print("✅ BOM généré : Traduit et optimisé pour GitHub.")


if __name__ == "__main__":
    generate_bom()
