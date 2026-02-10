import os, re, json, urllib.parse
from pathlib import Path

CFG = {
    "ext": ".stl", 
    "out": "BOM.md", 
    "json": "print_settings.json", 
    "root": "stl",
    "repo": "https://github.com",
    "branch": "main",
    "fields": ["perimetres", "couches_dessus", "couches_dessous", "remplissage", "motif_remplissage", "longueur_ancre", "longueur_max_ancre"]
}

def process_directory(current_dir, root_cat, data_json, md_list):
    """Fonction récursive pour parcourir les dossiers et fichiers."""
    # Séparer dossiers et fichiers STL
    items = sorted(list(current_dir.iterdir()))
    subdirs = [d for d in items if d.is_dir()]
    stls = [f for f in items if f.is_file() and f.suffix.lower() == CFG["ext"]]

    rel_to_cat = current_dir.relative_to(root_cat)
    depth = len(rel_to_cat.parts) if rel_to_cat != Path(".") else 0

    # 1. Afficher le dossier actuel (sauf si c'est la racine de la catégorie)
    if rel_to_cat != Path("."):
        indent = "&nbsp;&nbsp;" * (depth - 1)
        md_list.append(f"| | **{indent}└── 📁 {current_dir.name}** | | | | | | | |")

    # 2. Afficher les fichiers STL de ce dossier
    for stl_path in stls:
        path_str = stl_path.as_posix()
        info = data_json.setdefault(path_str, {f: None for f in CFG["fields"]})
        
        ok = all(info.get(f) not in (None, "") for f in CFG["fields"])
        qty = next(iter(re.findall(r'(?:x|qty)(\d+)', stl_path.name, re.I)), "1")
        
        indent_file = "&nbsp;&nbsp;&nbsp;&nbsp;" * depth + "📄 "
        layers = f"{info['couches_dessus'] or '-'}↑ {info['couches_dessous'] or '-'}↓"
        infill = f"{info['remplissage'] or '-'} ({info['motif_remplissage'] or '-'})"
        anchors = f"{info['longueur_ancre'] or '-'} ⇥ {info['longueur_max_ancre'] or '-'}"
        
        url_base = f"{CFG['repo']}/{{t}}/{CFG['branch']}/{urllib.parse.quote(path_str)}"
        
        md_list.append(f"| {'🟢' if ok else '🔴'} | {indent_file}<samp>{stl_path.name}</samp> | `x{qty}` | `{info['perimetres'] or '-'}` | `{layers}` | `{infill}` | `{anchors}` | [<samp>👁️ VUE</samp>]({url_base.format(t='blob')}) | [<samp>📥 STL</samp>]({url_base.format(t='raw')}) |")

    # 3. Descendre récursivement dans les sous-dossiers
    for subdir in subdirs:
        process_directory(subdir, root_cat, data_json, md_list)

def generate_bom():
    json_path = Path(CFG["json"])
    data_json = {}
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            data_json = json.load(f)

    md = ["# 📋 Nomenclature", "\n> `🟢` Configuré | `🔴` Incomplet\n"]
    root_dir = Path(CFG["root"])

    if not root_dir.exists():
        print(f"❌ Erreur: Dossier '{CFG['root']}' introuvable.")
        return

    categories = sorted([d for d in root_dir.iterdir() if d.is_dir()])

    for cat in categories:
        md.append(f"## 📦 {cat.name.upper()}")
        md.append("| Statut | Pièce | Qté | Périmètre | Couches | Remplissage | Ancre / Max | Voir | STL |")
        md.append("|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
        
        # Appel de la fonction récursive
        process_directory(cat, cat, data_json, md)
        
        md.append("\n---\n")

    with open(CFG["out"], "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data_json, f, indent=4, ensure_ascii=False)

    print(f"✅ {CFG['out']} généré avec succès.")

if __name__ == "__main__":
    generate_bom()
