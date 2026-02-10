import os, re, json, urllib.parse
from pathlib import Path

CFG = {
    "ext": ".stl", 
    "out": "BOM.md", 
    "json": "print_settings.json", 
    "root": "stl",
    "repo": "https://github.com/NZdesignch/asg-29-3d-printed",
    "branch": "main",
    "fields": ["perimetres", "couches_dessus", "couches_dessous", "remplissage", "motif_remplissage", "longueur_ancre", "longueur_max_ancre"]
}

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
        
         for root, _, files in os.walk(cat):
            curr_path = Path(root)
            stls = sorted([f for f in files if f.lower().endswith(CFG["ext"])])
            if not stls: continue

            rel_to_cat = curr_path.relative_to(cat)
            depth = len(rel_to_cat.parts) if rel_to_cat != Path(".") else 0
            
            # Affiche tous les dossiers dès le premier niveau
            if rel_to_cat != Path("."):
                # On retire 1 pour que le niveau 1 n'ait pas d'indentation
                indent = "&nbsp;&nbsp;" * (depth - 1)
                md.append(f"| | **{indent}└── 📁 {curr_path.name}** | | | | | | | |")

            for stl in stls:
                path_str = (curr_path / stl).as_posix()
                info = data_json.setdefault(path_str, {f: None for f in CFG["fields"]})
                
                ok = all(info.get(f) not in (None, "") for f in CFG["fields"])
                qty = next(iter(re.findall(r'(?:x|qty)(\d+)', stl, re.I)), "1")
                
                # Aligne l'icône du fichier selon la profondeur du dossier
                indent_file = "&nbsp;&nbsp;&nbsp;&nbsp;" * depth + "📄 "
                
                layers = f"{info['couches_dessus'] or '-'}↑ {info['couches_dessous'] or '-'}↓"
                infill = f"{info['remplissage'] or '-'} ({info['motif_remplissage'] or '-'})"
                anchors = f"{info['longueur_ancre'] or '-'} ⇥ {info['longueur_max_ancre'] or '-'}"
                
                url_base = f"{CFG['repo']}/{{t}}/{CFG['branch']}/{urllib.parse.quote(path_str)}"
                
                md.append(f"| {'🟢' if ok else '🔴'} | {indent_file}<samp>{stl}</samp> | `x{qty}` | `{info['perimetres'] or '-'}` | `{layers}` | `{infill}` | `{anchors}` | [<samp>👁️ VUE</samp>]({url_base.format(t='blob')}) | [<samp>📥 STL</samp>]({url_base.format(t='raw')}) |")
        md.append("\n---\n")

    with open(CFG["out"], "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data_json, f, indent=4, ensure_ascii=False)

    print(f"✅ {CFG['out']} mis à jour.")

if __name__ == "__main__":
    generate_bom()
