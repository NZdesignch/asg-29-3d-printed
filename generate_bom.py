import json, re, urllib.parse
from pathlib import Path

# --- Configuration ---
CFG = {
    "ext": ".stl", "out": "BOM.md", "json": "print_settings.json", "root": "stl",
    "repo": "https://github.com", "branch": "main",
    "fields": ["perimetres", "couches_dessus", "couches_dessous", "remplissage", 
               "motif_remplissage", "longueur_ancre", "longueur_max_ancre"]
}

RE_QTY = re.compile(r'(?:x|qty)(\d+)', re.IGNORECASE)

def natural_key(path):
    """Clé de tri pour classer '2' avant '10'."""
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r'(\d+)', path.name)]

def generate_bom():
    ROOT_DIR, JSON_PATH = Path(CFG["root"]), Path(CFG["json"])
    FIELDS, EMPTY_INFO = CFG["fields"], {f: None for f in CFG["fields"]}
    
    if not ROOT_DIR.exists(): return print("❌ Dossier racine introuvable")

    # 1. Chargement & Préparation
    try:
        db = json.loads(JSON_PATH.read_text(encoding="utf-8")) if JSON_PATH.exists() else {}
    except: db = {}
    
    md = ["# 📋 Nomenclature", "\n> `🟢` Configuré | `🔴` Incomplet\n"]
    url_template = f"{CFG['repo']}/{{}}/{CFG['branch']}/"
    
    # Set pour suivre les fichiers vus (pour le nettoyage)
    seen_files = set()

    # 2. Parcours des catégories (Dossiers de premier niveau)
    categories = sorted((d for d in ROOT_DIR.iterdir() if d.is_dir()), key=natural_key)

    for cat in categories:
        md.extend([f"## 📦 {cat.name.upper()}", 
                   "| Statut | Pièce | Qté | Périmètre | Couches | Remplissage | Ancre | Voir |",
                   "|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|"])

        # Parcours récursif des fichiers STL
        for stl in sorted(cat.rglob(f"*{CFG['ext']}"), key=natural_key):
            path_str = stl.as_posix()
            seen_files.add(path_str) # Marquer comme présent
            
            info = db.setdefault(path_str, EMPTY_INFO.copy())
            ok = '🟢' if all(info.get(f) for f in FIELDS) else '🔴'
            
            # Analyse data
            qty = (RE_QTY.search(stl.name) or [0, "1"])[1]
            depth = len(stl.relative_to(cat).parts) - 1
            indent = f"{'&nbsp;' * (4 * depth)}📄 "
            
            # URL
            encoded_path = urllib.parse.quote(path_str)
            base_url = url_template + encoded_path

            md.append(
                f"| {ok} | {indent}<samp>{stl.name}</samp> | `x{qty}` | "
                f"`{info['perimetres'] or '-'}` | "
                f"`{info['couches_dessus'] or '-'}↑ {info['couches_dessous'] or '-'}↓` | "
                f"`{info['remplissage'] or '-'}` | `{info['longueur_ancre'] or '-'}` | "
                f"[👁️]({base_url.format('blob')}) |"
            )
        md.append("\n---\n")

    # 3. NETTOYAGE : Supprimer les entrées JSON dont le fichier n'existe plus
    removed_count = 0
    for path_in_db in list(db.keys()):
        if path_in_db not in seen_files:
            del db[path_in_db]
            removed_count += 1

    # 4. Sauvegarde
    JSON_PATH.write_text(json.dumps(db, indent=4, ensure_ascii=False), encoding="utf-8")
    Path(CFG["out"]).write_text("\n".join(md), encoding="utf-8")
    
    status_msg = f"✅ BOM généré. {len(seen_files)} fichiers traités."
    if removed_count: status_msg += f" ({removed_count} entrées obsolètes nettoyées)"
    print(status_msg)

if __name__ == "__main__":
    generate_bom()
