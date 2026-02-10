import json
import re
import urllib.parse
from pathlib import Path

# --- Configuration (Constantes) ---
CFG = {
    "ext": ".stl", "out": "BOM.md", "json": "print_settings.json", "root": "stl",
    "repo": "https://github.com", "branch": "main",
    "fields": ["perimetres", "couches_dessus", "couches_dessous", "remplissage", 
               "motif_remplissage", "longueur_ancre", "longueur_max_ancre"]
}

# Pré-compilation pour la performance
RE_QTY = re.compile(r'(?:x|qty)(\d+)', re.IGNORECASE)

def format_md_row(stl_path, info, depth):
    """S'occupe uniquement du formatage d'une ligne du tableau."""
    ok = all(info.get(f) not in (None, "") for f in CFG["fields"])
    qty_match = RE_QTY.search(stl_path.name)
    qty = qty_match.group(1) if qty_match else "1"
    
    indent = "&nbsp;" * 4 * depth + "📄 "
    layers = f"{info['couches_dessus'] or '-'}↑ {info['couches_dessous'] or '-'}↓"
    infill = f"{info['remplissage'] or '-'} ({info['motif_remplissage'] or '-'})"
    anchors = f"{info['longueur_ancre'] or '-'} ⇥ {info['longueur_max_ancre'] or '-'}"
    
    encoded_path = urllib.parse.quote(stl_path.as_posix())
    base_url = f"{CFG['repo']}/{{}}/{CFG['branch']}/{encoded_path}"
    
    return (f"| {'🟢' if ok else '🔴'} | {indent}<samp>{stl_path.name}</samp> | `x{qty}` | "
            f"`{info['perimetres'] or '-'}` | `{layers}` | `{infill}` | `{anchors}` | "
            f"[<samp>👁️ VUE</samp>]({base_url.format('blob')}) | [<samp>📥 STL</samp>]({base_url.format('raw')}) |")

def process_directory(current_dir, root_cat, data_json, md_list):
    """Parcours récursif optimisé."""
    # On itère une seule fois sur le dossier
    for item in sorted(current_dir.iterdir(), key=lambda x: x.name.lower()):
        rel_to_cat = item.relative_to(root_cat)
        depth = len(rel_to_cat.parts) - 1

        if item.is_dir():
            indent = "&nbsp;" * 2 * depth
            md_list.append(f"| | **{indent}└── 📁 {item.name}** | | | | | | | |")
            process_directory(item, root_cat, data_json, md_list)
            
        elif item.suffix.lower() == CFG["ext"]:
            path_str = item.as_posix()
            info = data_json.setdefault(path_str, {f: None for f in CFG["fields"]})
            md_list.append(format_md_row(item, info, depth))

def generate_bom():
    root_dir = Path(CFG["root"])
    json_file = Path(CFG["json"])
    
    if not root_dir.exists():
        print(f"❌ Erreur: Dossier '{CFG['root']}' introuvable.")
        return

    # Chargement sécurisé
    data_json = {}
    if json_file.exists():
        try:
            data_json = json.loads(json_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("⚠️ Fichier JSON corrompu, création d'un nouveau.")

    md = ["# 📋 Nomenclature", "\n> `🟢` Configuré | `🔴` Incomplet\n"]

    for cat in sorted(d for d in root_dir.iterdir() if d.is_dir()):
        md.extend([f"## 📦 {cat.name.upper()}", 
                   "| Statut | Pièce | Qté | Périmètre | Couches | Remplissage | Ancre / Max | Voir | STL |",
                   "|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"])
        process_directory(cat, cat, data_json, md)
        md.append("\n---\n")

    # Écritures
    Path(CFG["out"]).write_text("\n".join(md), encoding="utf-8")
    json_file.write_text(json.dumps(data_json, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Terminé : {CFG['out']} et {CFG['json']} mis à jour.")

if __name__ == "__main__":
    generate_bom()
