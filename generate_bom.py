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

# Pré-compilation du Regex (Performance)
RE_QTY = re.compile(r'(?:x|qty)(\d+)', re.IGNORECASE)

def get_stl_data(path_str, data_json):
    """Récupère et initialise les données JSON pour un fichier."""
    info = data_json.setdefault(path_str, {f: None for f in CFG["fields"]})
    is_ok = all(info.get(f) not in (None, "") for f in CFG["fields"])
    return info, is_ok

def process_directory(current_dir, root_cat, data_json, md_list):
    """Parcours récursif optimisé."""
    # Itérateur au lieu de listes pour économiser la mémoire
    items = sorted(current_dir.iterdir())
    
    rel_to_cat = current_dir.relative_to(root_cat)
    depth = len(rel_to_cat.parts) if rel_to_cat != Path(".") else 0

    if rel_to_cat != Path("."):
        indent = "&nbsp;&nbsp;" * (depth - 1)
        md_list.append(f"| | **{indent}└── 📁 {current_dir.name}** | | | | | | | |")

    for item in items:
        if item.is_dir():
            process_directory(item, root_cat, data_json, md_list)
        elif item.suffix.lower() == CFG["ext"]:
            path_str = item.as_posix()
            info, ok = get_stl_data(path_str, data_json)
            
            # Extraction Qté
            qty_match = RE_QTY.search(item.name)
            qty = qty_match.group(1) if qty_match else "1"
            
            # Formatage des champs
            layers = f"{info['couches_dessus'] or '-'}↑ {info['couches_dessous'] or '-'}↓"
            infill = f"{info['remplissage'] or '-'} ({info['motif_remplissage'] or '-'})"
            anchors = f"{info['longueur_ancre'] or '-'} ⇥ {info['longueur_max_ancre'] or '-'}"
            
            # URL encodée
            encoded_path = urllib.parse.quote(path_str)
            url_raw = f"{CFG['repo']}/raw/{CFG['branch']}/{encoded_path}"
            url_view = f"{CFG['repo']}/blob/{CFG['branch']}/{encoded_path}"
            
            indent_file = "&nbsp;&nbsp;&nbsp;&nbsp;" * depth + "📄 "
            status = '🟢' if ok else '🔴'
            
            md_list.append(
                f"| {status} | {indent_file}<samp>{item.name}</samp> | `x{qty}` | "
                f"`{info['perimetres'] or '-'}` | `{layers}` | `{infill}` | "
                f"`{anchors}` | [<samp>👁️ VUE</samp>]({url_view}) | [<samp>📥 STL</samp>]({url_raw}) |"
            )

def generate_bom():
    root_path = Path(CFG["root"])
    if not root_path.exists():
        print(f"❌ Erreur: '{CFG['root']}' introuvable.")
        return

    # Chargement sécurisé du JSON
    try:
        data_json = json.loads(Path(CFG["json"]).read_text(encoding="utf-8")) if Path(CFG["json"]).exists() else {}
    except json.JSONDecodeError:
        data_json = {}

    md = ["# 📋 Nomenclature", "\n> `🟢` Configuré | `🔴` Incomplet\n"]

    for cat in sorted(d for d in root_path.iterdir() if d.is_dir()):
        md.extend([
            f"## 📦 {cat.name.upper()}",
            "| Statut | Pièce | Qté | Périmètre | Couches | Remplissage | Ancre / Max | Voir | STL |",
            "|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"
        ])
        process_directory(cat, cat, data_json, md)
        md.append("\n---\n")

    # Écritures finales
    Path(CFG["out"]).write_text("\n".join(md), encoding="utf-8")
    Path(CFG["json"]).write_text(json.dumps(data_json, indent=4, ensure_ascii=False), encoding="utf-8")
    
    print(f"✅ {CFG['out']} généré.")

if __name__ == "__main__":
    generate_bom()
