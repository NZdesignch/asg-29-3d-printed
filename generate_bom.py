#!/usr/bin/env python3
"""
generate_bom.py
---------------
À placer à la racine du dépôt GitHub.

Scanne le dossier `stl/` du repo (arborescence profonde, 4+ niveaux),
lit un fichier JSON global à la racine avec les paramètres d'impression,
et génère bom.md à la racine du repo.

Usage local :
    python generate_bom.py --repo-url https://github.com/user/repo

Usage GitHub Actions :
    python generate_bom.py --repo-root $GITHUB_WORKSPACE
    (l'URL est détectée automatiquement via $GITHUB_SERVER_URL / $GITHUB_REPOSITORY)
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


# ─────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────

COLONNES = {
    "infill_percentage": "% Remplissage",
    "infill_type":       "Type Remplissage",
    "top_layers":        "Couches Dessus",
    "bottom_layers":     "Couches Dessous",
    "anchor_length":     "Ancre (mm)",
    "anchor_length_max": "Ancre Max (mm)",
}

VALEUR_MANQUANTE = "—"
IGNORED_DIRS = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv"}

# Icônes colonnes viewer / téléchargement
ICON_VIEW     = "🔍"
ICON_DOWNLOAD = "⬇️"


# ─────────────────────────────────────────────────────────────────
# Chargement JSON
# ─────────────────────────────────────────────────────────────────

def load_json(json_path: Path) -> dict:
    if not json_path.exists():
        print(f"[AVERTISSEMENT] Fichier JSON introuvable : {json_path}", file=sys.stderr)
        return {}
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    print(f"[INFO] JSON chargé : {json_path}  ({len(data)} entrée(s))")
    return data


# ─────────────────────────────────────────────────────────────────
# Construction des URLs GitHub
# ─────────────────────────────────────────────────────────────────

def make_github_urls(repo_url: str, branch: str, rel_posix: str) -> tuple[str, str]:
    """
    Retourne (url_viewer, url_raw) pour un fichier STL.
    - url_viewer  : https://github.com/user/repo/blob/main/stl/...stl
                    GitHub affiche le viewer 3D natif sur cette URL.
    - url_raw     : https://raw.githubusercontent.com/user/repo/main/stl/...stl
                    Lien de téléchargement direct.
    """
    base       = repo_url.rstrip("/")
    # Convertir github.com → raw.githubusercontent.com
    raw_base   = base.replace("https://github.com/", "https://raw.githubusercontent.com/")

    url_viewer = f"{base}/blob/{branch}/{rel_posix}"
    url_raw    = f"{raw_base}/{branch}/{rel_posix}"
    return url_viewer, url_raw


# ─────────────────────────────────────────────────────────────────
# Scan des fichiers STL
# ─────────────────────────────────────────────────────────────────

def find_stl_files(scan_root: Path) -> dict:
    groups = defaultdict(list)
    for dirpath, dirnames, filenames in os.walk(scan_root):
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORED_DIRS)
        current = Path(dirpath)
        for fname in sorted(filenames):
            if not fname.lower().endswith(".stl"):
                continue
            f   = current / fname
            rel = f.relative_to(scan_root)
            top = "_racine" if len(rel.parts) == 1 else rel.parts[0]
            groups[top].append(f)
    return dict(sorted(groups.items()))


# ─────────────────────────────────────────────────────────────────
# Résolution des paramètres d'impression
# ─────────────────────────────────────────────────────────────────

def get_params(file_path: Path, repo_root: Path, json_data: dict) -> dict:
    try:
        rel_posix = file_path.relative_to(repo_root).as_posix()
    except ValueError:
        rel_posix = file_path.as_posix()

    for candidate in [rel_posix, str(Path(rel_posix).with_suffix("")),
                      file_path.name, file_path.stem]:
        if candidate in json_data:
            return json_data[candidate]

    for key, val in json_data.items():
        kp = Path(key)
        if kp.name == file_path.name or kp.stem == file_path.stem:
            return val
    return {}


# ─────────────────────────────────────────────────────────────────
# Arbre de fichiers
# ─────────────────────────────────────────────────────────────────

def build_tree(files: list, scan_root: Path) -> dict:
    tree = {"__files__": []}
    for f in files:
        rel   = f.relative_to(scan_root)
        node  = tree
        for part in rel.parts[:-1]:
            node = node.setdefault(part, {"__files__": []})
        node["__files__"].append(f)
    return tree


def flatten_tree(node: dict, prefix: str = "", depth: int = 0) -> list:
    rows    = []
    subdirs = {k: v for k, v in node.items() if k != "__files__"}
    files   = node["__files__"]
    items   = list(subdirs.items()) + [("__file__", f) for f in files]
    total   = len(items)

    for idx, item in enumerate(items):
        is_last   = (idx == total - 1)
        connector = "└── " if is_last else "├── "

        if isinstance(item[1], dict):
            rows.append(("dossier", item[0], depth, prefix, is_last))
            child_prefix = prefix + ("    " if is_last else "│   ")
            rows.extend(flatten_tree(item[1], child_prefix, depth + 1))
        else:
            rows.append(("fichier", item[1], depth, prefix, is_last))

    return rows


# ─────────────────────────────────────────────────────────────────
# Construction du tableau Markdown
# ─────────────────────────────────────────────────────────────────

def format_value(val) -> str:
    if val is None:
        return VALEUR_MANQUANTE
    if isinstance(val, bool):
        return "Oui" if val else "Non"
    if isinstance(val, float):
        return f"{val:g}"
    return str(val)


def build_table(files: list, json_data: dict, repo_root: Path, scan_root: Path,
                top_folder: str, repo_url: str, branch: str) -> str:

    col_keys   = list(COLONNES.keys())
    col_titles = list(COLONNES.values())

    has_links = bool(repo_url)

    # En-tête : colonnes fixes + params + liens (si URL dispo)
    link_cols  = f" {ICON_VIEW} | {ICON_DOWNLOAD} |" if has_links else ""
    link_sep   = " :---: | :---: |"               if has_links else ""
    header     = f"| Structure | Fichier | " + " | ".join(col_titles) + f" |{link_cols}"
    separator  = f"|-----------|---------|" + "|".join([":------:"] * len(col_keys)) + f"|{link_sep}"
    rows       = [header, separator]

    subtree_root = scan_root if top_folder == "_racine" else scan_root / top_folder
    tree         = build_tree(files, subtree_root)
    flat         = flatten_tree(tree)

    for kind, data, depth, prefix, is_last in flat:
        connector = "└── " if is_last else "├── "
        tree_str  = prefix + connector

        if kind == "dossier":
            empty     = " | ".join([" "] * len(col_keys))
            link_cell = " |  |  |" if has_links else ""
            rows.append(f"| `{tree_str}{data}/` | | {empty} |{link_cell}")
        else:
            f      = data
            params = get_params(f, repo_root, json_data)
            values = [format_value(params.get(k)) for k in col_keys]

            if has_links:
                try:
                    rel_posix = f.relative_to(repo_root).as_posix()
                except ValueError:
                    rel_posix = f.name
                url_view, url_raw = make_github_urls(repo_url, branch, rel_posix)
                link_cell = f" [{ICON_VIEW}]({url_view}) | [{ICON_DOWNLOAD}]({url_raw}) |"
            else:
                link_cell = ""

            rows.append(
                f"| `{tree_str}{f.name}` | `{f.name}` | "
                + " | ".join(values)
                + f" |{link_cell}"
            )

    return "\n".join(rows)


# ─────────────────────────────────────────────────────────────────
# Génération du bom.md
# ─────────────────────────────────────────────────────────────────

def generate_bom(repo_root: Path, json_data: dict, scan_root: Path,
                 output: Path, repo_url: str, branch: str) -> None:

    groups = find_stl_files(scan_root)
    total  = sum(len(v) for v in groups.values())

    if not groups:
        print("[AVERTISSEMENT] Aucun fichier STL trouvé.", file=sys.stderr)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Bill of Materials (BOM)",
        "",
        "<!-- Généré automatiquement par generate_bom.py — ne pas éditer manuellement -->",
        "",
        "| | |",
        "|---|---|",
        f"| **Généré le** | {now} |",
        f"| **Dossier scanné** | `{scan_root.relative_to(repo_root).as_posix()}` |",
        f"| **Total fichiers STL** | {total} |",
        f"| **Groupes** | {len(groups)} |",
        "",
    ]

    # Table des matières
    lines += ["## Table des matières", ""]
    for top in groups:
        display = top if top != "_racine" else "Racine"
        anchor  = display.lower().replace(" ", "-").replace("_", "-")
        lines.append(f"- [{display}](#{anchor}) — {len(groups[top])} fichier(s)")
    lines += ["", "---", ""]

    # Sections
    for top_folder, files in groups.items():
        display = top_folder if top_folder != "_racine" else "Racine"

        lines += [
            f"## {display}",
            "",
            f"_{len(files)} fichier(s) STL_",
            "",
            build_table(files, json_data, repo_root, scan_root,
                        top_folder, repo_url, branch),
            "",
            "---",
            "",
        ]

    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] {output.name} généré — {total} STL dans {len(groups)} groupe(s)")


# ─────────────────────────────────────────────────────────────────
# Point d'entrée
# ─────────────────────────────────────────────────────────────────

def main():
    # Détection automatique de l'URL en contexte GitHub Actions
    gh_server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    gh_repo   = os.environ.get("GITHUB_REPOSITORY", "")
    gh_branch = os.environ.get("GITHUB_REF_NAME", "main")
    auto_url  = f"{gh_server}/{gh_repo}" if gh_repo else ""

    script_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(
        description="Génère bom.md depuis les fichiers STL du dossier stl/ + JSON global."
    )
    parser.add_argument("--repo-root", type=Path, default=script_dir,
                        help="Racine du dépôt Git (défaut : dossier du script)")
    parser.add_argument("--json", type=str, default="params.json",
                        help="Nom du fichier JSON à la racine (défaut : params.json)")
    parser.add_argument("--output", type=str, default="bom.md",
                        help="Nom du fichier de sortie (défaut : bom.md)")
    parser.add_argument("--stl-dir", type=str, default="stl",
                        help="Sous-dossier à scanner (défaut : stl)")
    parser.add_argument("--repo-url", type=str, default=auto_url,
                        help="URL du repo GitHub (ex: https://github.com/user/repo)")
    parser.add_argument("--branch", type=str, default=gh_branch,
                        help="Branche courante (défaut : main ou $GITHUB_REF_NAME)")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    if not repo_root.is_dir():
        print(f"[ERREUR] Racine du repo introuvable : {repo_root}", file=sys.stderr)
        sys.exit(1)

    scan_root = repo_root / args.stl_dir
    if not scan_root.is_dir():
        print(f"[ERREUR] Dossier à scanner introuvable : {scan_root}", file=sys.stderr)
        sys.exit(1)

    if not args.repo_url:
        print("[AVERTISSEMENT] --repo-url non fourni : les colonnes 🔍 et ⬇️ seront absentes.",
              file=sys.stderr)

    json_data = load_json(repo_root / args.json)
    generate_bom(repo_root, json_data, scan_root,
                 repo_root / args.output, args.repo_url, args.branch)


if __name__ == "__main__":
    main()
