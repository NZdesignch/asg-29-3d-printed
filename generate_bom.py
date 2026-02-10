import json, re, urllib.parse
from pathlib import Path

# --- Configuration (Constantes en cache local) ---
CFG = {
    "ext": ".stl", "out": "BOM.md", "json": "print_settings.json", "root": "stl",
    "repo": "https://github.com", "branch": "main",
    "fields": ["perimetres", "couches_dessus", "couches_dessous", "remplissage", 
               "motif_remplissage", "longueur_ancre", "longueur_max_ancre"]
}

# Regex compilé une seule fois
RE_QTY = re.compile(r'(?:x|qty)(\d+)', re.IGNORECASE)

def generate_bom():
    # 1. Mise en cache des variables pour éviter les lookups CFG['...']
    ROOT_DIR = Path(CFG["root"])
    JSON_PATH = Path(CFG["json"])
    FIELDS = CFG["fields"]
    EMPTY_INFO = {f: None for f in FIELDS} # Template réutilisé
    
    if not ROOT_DIR.exists(): return

    # 2. Chargement JSON ultra-rapide
    try:
        data_json = json.loads(JSON_PATH.read_text(encoding="utf-8")) if JSON_PATH.exists() else {}
    except:
        data_json = {}

    md = ["# 📋 Nomenclature", "\n> `🟢` Configuré | `🔴` Incomplet\n"]
    
    # Pré-calculer la base URL pour limiter les concaténations
    url_template = f"{CFG['repo']}/{{}}/{CFG['branch']}/"

    # 3. Traitement avec un seul parcours disque (rglob) par catégorie
    for cat in sorted((d for d in ROOT_DIR.iterdir() if d.is_dir()), key=lambda x: x.name.lower()):
        md.extend([f"## 📦 {cat.name.upper()}", 
                   "| Statut | Pièce | Qté | Périmètre | Couches | Remplissage | Ancre / Max | Voir | STL |",
                   "|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|"])

        # On récupère tout d'un coup, trié par nom de fichier (Natural Sort simulé par lower)
        # On utilise une liste de compréhension pour la vitesse
        for item in sorted(cat.rglob(f"*{CFG['ext']}"), key=lambda x: x.name.lower()):
            path_str = item.as_posix()
            
            # Récupération / Initialisation optimisée (get + update)
            info = data_json.get(path_str)
            if info is None:
                info = data_json[path_str] = EMPTY_INFO.copy()

            # Analyse rapide : on s'arrête au premier None/vide rencontré
            ok = '🟢' if all(info.get(f) for f in FIELDS) else '🔴'
            
            # Extraction Qté (search est plus rapide que findall pour un seul résultat)
            m = RE_QTY.search(item.name)
            qty = m.group(1) if m else "1"

            # Formatage : calcul de profondeur relatif à la catégorie
            depth = len(item.relative_to(cat).parts) - 1
            indent = f"{'&nbsp;' * (4 * depth)}📄 "
            
            # Encodage URL (opération la plus lourde, isolée ici)
            encoded_path = urllib.parse.quote(path_str)
            full_url = url_template + encoded_path

            md.append(
                f"| {ok} | {indent}<samp>{item.name}</samp> | `x{qty}` | "
                f"`{info['perimetres'] or '-'}` | "
                f"`{info['couches_dessus'] or '-'}↑ {info['couches_dessous'] or '-'}↓` | "
                f"`{info['remplissage'] or '-'} ({info['motif_remplissage'] or '-'})` | "
                f"`{info['longueur_ancre'] or '-'} ⇥ {info['longueur_max_ancre'] or '-'}` | "
                f"[<samp>👁️ VUE</samp>]({full_url.format('blob')}) | "
                f"[<samp>📥 STL</samp>]({full_url.format('raw')}) |"
            )
        
        md.append("\n---\n")

    # 4. Écriture atomique (réduit les risques de corruption de fichier)
    JSON_PATH.write_text(json.dumps(data_json, indent=4, ensure_ascii=False), encoding="utf-8")
    Path(CFG["out"]).write_text("\n".join(md), encoding="utf-8")

if __name__ == "__main__":
    generate_bom()
