import json
import re
import urllib.parse
from pathlib import Path

# --- Configuration ---
CFG = {
    "ext": ".stl", "out": "BOM.md", "json": "print_settings.json", "root": "stl",
    "repo": "https://github.com", "branch": "main",
    "fields": ["perimetres", "couches_dessus", "couches_dessous", "remplissage", 
               "motif_remplissage", "longueur_ancre", "longueur_max_ancre"]
}

RE_QTY = re.compile(r'(?:x|qty)(\d+)', re.IGNORECASE)

def format_md_row(stl_path, info, depth, fields, repo_url):
    """Version optimisée du formatage de ligne."""
    # all() s'arrête dès qu'un élément est faux (Lazy evaluation)
    ok = all(info.get(f) not in (None, "") for f in fields)
    
    qty_match = RE_QTY.search(stl_path.name)
    qty = qty_match.group(1) if qty_match else "1"
    
    # Construction de chaîne plus rapide (f-strings optimisées)
    indent = f"{'&nbsp;' * (4 * depth)}📄 "
    layers = f"{info['couches_dessus'] or '-'}↑ {info['couches_dessous'] or '-'}↓"
    infill = f"{info['remplissage'] or '-'} ({info['motif_remplissage'] or '-'})"
    anchors = f"{info['longueur_ancre'] or '-'} ⇥ {info['longueur_max_ancre'] or '-'}"
    
    encoded_path = urllib.parse.quote(stl_path.as_posix())
    # Pré-formatage partiel de l'URL
    url_common = f"{repo_url}/{{}}/{CFG['branch']}/{encoded_path}"
    
    return (f"| {'🟢' if ok else '🔴'} | {indent}<samp>{stl_path.name}</samp> | `x{qty}` | "
            f"`{info['perimetres'] or '-'}` | `{layers}` | `{infill}` | `{anchors}` | "
            f"[<samp>👁️ VUE</samp>]({url_common.format('blob')}) | [<samp>📥 STL</samp>]({url_common.format('raw')}) |")

def process_directory(current_dir, root_cat, data_json, md_list, fields, repo_url, ext):
    """Parcours récursif avec injection de variables pour éviter les lookups globaux."""
    # Utilisation d'un itérateur trié
    for item in sorted(current_dir.iterdir(), key=lambda x: x.name.lower()):
        # Calcul de la profondeur une seule fois par item
        rel_parts = item.relative_to(root_cat).parts
        depth = len(rel_parts) - 1

        if item.is_dir():
            indent = "&nbsp;" * (2 * depth)
            md_list.append(f"| | **{indent}└── 📁 {item.name}** | | | | | | | |")
            process_directory(item, root_cat, data_json, md_list, fields, repo_url, ext)
            
        elif item.suffix.lower() == ext:
            path_str = item.as_posix()
            # Initialisation plus propre du dictionnaire
            if path_str not in data_json:
                data_json[path_str] = {f: None for f in fields}
            
            md_list.append(format_md_row(item, data_json[path_str], depth, fields, repo_url))

def generate_bom():
    # Cache local des variables CFG (vitesse)
    root_dir = Path(CFG["root"])
    json_path = Path(CFG["json"])
    fields = CFG["fields"]
    repo_url = CFG["repo"]
    ext = CFG["ext"]
    
    if not root_dir.exists():
        print(f"❌ Erreur: Dossier '{CFG['root']}' introuvable.")
        return

    # Lecture JSON optimisée
    data_json = {}
    if json_path.exists():
        try:
            data_json = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            pass

    # Utilisation d'une liste pour accumuler les lignes (beaucoup plus rapide que += sur string)
    md = ["# 📋 Nomenclature", "\n> `🟢` Configuré | `🔴` Incomplet\n"]

    # Traitement des catégories
    for cat in sorted((d for d in root_dir.iterdir() if d.is_dir()), key=lambda x: x.name.lower()):
        md.extend([
            f"## 📦 {cat.name.upper()}", 
            "| Statut | Pièce | Qté | Périmètre | Couches | Remplissage | Ancre / Max | Voir | STL |",
            "|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"
        ])
        process_directory(cat, cat, data_json, md, fields, repo_url, ext)
        md.append("\n---\n")

    # Écritures groupées (Atomic write style)
    json_path.write_text(json.dumps(data_json, indent=4, ensure_ascii=False), encoding="utf-8")
    Path(CFG["out"]).write_text("\n".join(md), encoding="utf-8")
    
    print(f"✅ {CFG['out']} mis à jour.")

if __name__ == "__main__":
    generate_bom()
