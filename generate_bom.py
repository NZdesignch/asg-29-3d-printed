import json, re, urllib.parse
from pathlib import Path

# Config
ROOT, DB_FILE, OUT_FILE = Path("stl"), Path("print_settings.json"), Path("BOM.md")
BASE_URL = "https://github.com"
FIELDS = ["perimetres", "couches_dessus", "couches_dessous", "remplissage", "motif_remplissage", "longueur_ancre", "longueur_max_ancre"]

def natural_key(path):
    """Clé pour trier 'pièce_2' avant 'pièce_10'."""
    return [int(s) if s.isdigit() else s.lower() for s in re.split(r'(\d+)', path.name)]

def simplify():
    if not ROOT.exists(): return print("❌ Dossier introuvable")

    db = json.loads(DB_FILE.read_text()) if DB_FILE.exists() else {}
    md = ["# 📋 Nomenclature\n> 🟢 OK | 🔴 Incomplet\n"]

    # Tri naturel des dossiers catégories
    for cat in sorted((d for d in ROOT.iterdir() if d.is_dir()), key=natural_key):
        md += [f"## 📦 {cat.name.upper()}", "| Statut | Pièce | Qté | Périmètre | Couches | Remplissage | Ancre | Voir |", "|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|"]
        
        # Tri naturel des fichiers STL récursifs
        for stl in sorted(cat.rglob("*.stl"), key=natural_key):
            rel_path = stl.as_posix()
            info = db.setdefault(rel_path, {f: None for f in FIELDS})
            
            qty = (re.findall(r'(?:x|qty)(\d+)', stl.name, re.I) or ["1"])[0]
            ok = all(info.values())
            
            depth = len(stl.relative_to(cat).parts) - 1
            name = f"{'&nbsp;'*4*depth}📄 <samp>{stl.name}</samp>"
            url = f"{BASE_URL}/{urllib.parse.quote(rel_path)}"
            
            md.append(f"| {'🟢' if ok else '🔴'} | {name} | `x{qty}` | `{info['perimetres'] or '-'}` | "
                      f"`{info['couches_dessus'] or '-'}↑ {info['couches_dessous'] or '-'}↓` | "
                      f"`{info['remplissage'] or '-'}` | `{info['longueur_ancre'] or '-'}` | [👁️]({url}) |")
        
        md.append("\n---\n")

    OUT_FILE.write_text("\n".join(md), encoding="utf-8")
    DB_FILE.write_text(json.dumps(db, indent=4), encoding="utf-8")
    print(f"✅ BOM généré avec **tri naturel**.")

if __name__ == "__main__":
    simplify()
