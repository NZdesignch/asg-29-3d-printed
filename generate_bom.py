import os, re, json, urllib.parse

CFG = {
    "ext": ".stl", "out": "BOM.md", "json": "print_settings.json", "root": "stl",
    "repo": "https://github.com", "branch": "main",
    "fields": ["perimetres", "couches_dessus", "couches_dessous", "remplissage", "motif_remplissage", "longueur_ancre", "longueur_max_ancre"]
}

def generate_bom():
    data_json = json.load(open(CFG["json"], "r", encoding="utf-8")) if os.path.exists(CFG["json"]) else {}
    md = [f"# ✈️ Nomenclature ASG 29\n\n> `🟢` Configuré | `🔴` Incomplet\n"]
    
    categories = sorted([d for d in os.listdir(CFG["root"]) if os.path.isdir(os.path.join(CFG["root"], d))])

    for cat in categories:
        cat_path = os.path.join(CFG["root"], cat)
        md.append(f"## 📦 {cat.upper()}\n\n| Statut | Pièce | Qté | Périm. | Haut/Bas | Rempl. (Motif) | Ancres | Voir | STL |\n|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
        
        for root, dirs, files in os.walk(cat_path):
            stls = sorted([f for f in files if f.lower().endswith(CFG["ext"])])
            if not stls: continue

            # Gestion de la hiérarchie visuelle
            rel_path = os.path.relpath(root, cat_path).replace("\\", "/")
            if rel_path != ".":
                depth = rel_path.count('/')
                indent = "&nbsp;&nbsp;" * depth + "└── 📁 "
                md.append(f"| | **{indent}{os.path.basename(root)}** | | | | | | | |")

            for stl in stls:
                full_path = os.path.join(root, stl).replace("\\", "/")
                info = data_json.setdefault(full_path, {f: None for f in CFG["fields"]})
                
                # Validation et Quantité
                ok = all(info.get(f) not in [None, ""] for f in CFG["fields"])
                qty = (re.findall(r'(?:x|qty)(\d+)', stl, re.I) + ["1"])[0]
                
                # Formatage cellules
                depth_file = 0 if rel_path == "." else rel_path.count('/') + 1
                indent_file = "&nbsp;&nbsp;&nbsp;&nbsp;" * depth_file + "📄 "
                layers = f"{info['couches_dessus'] or '-'}↑ {info['couches_dessous'] or '-'}↓"
                infill = f"{info['remplissage'] or '-'} ({info['motif_remplissage'] or '-'})"
                anchors = f"{info['longueur_ancre'] or '-'} ➜ {info['longueur_max_ancre'] or '-'}"
                
                url = f"{CFG['repo']}/{{t}}/{CFG['branch']}/{urllib.parse.quote(full_path)}"
                
                md.append(f"| {'🟢' if ok else '🔴'} | {indent_file}<samp>{stl}</samp> | `x{qty}` | `{info['perimetres'] or '-'}` | `{layers}` | `{infill}` | `{anchors}` | [<samp>👁️ VUE</samp>]({url.format(t='blob')}) | [<samp>📥 STL</samp>]({url.format(t='raw')}) |")
        md.append("\n---\n")

    with open(CFG["out"], "w", encoding="utf-8") as f: f.write("\n".join(md))
    with open(CFG["json"], "w", encoding="utf-8") as f: json.dump(data_json, f, indent=4, ensure_ascii=False)
    print("✅ BOM Multi-niveaux généré.")

if __name__ == "__main__":
    generate_bom()
