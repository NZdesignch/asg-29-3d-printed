import os
from pathlib import Path
import urllib.parse

def get_icon(path):
    return "📁" if path.is_dir() else "📄"

def generate_bom():
    root_dir = Path(".")
    output_file = "bom.md"
    exclude = {'.git', '.github', '__pycache__', '.vscode', 'venv'}

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🛠️ Bill of Materials (BOM) Multi-niveaux\n\n")
        
        # --- SECTION 1 : Tableaux par dossier de Niveau 1 ---
        f.write("## 📂 Par Catégories Principales\n\n")
        top_folders = sorted([d for d in root_dir.iterdir() if d.is_dir() and d.name not in exclude])
        
        for folder in top_folders:
            stls = sorted(list(folder.rglob("*.stl")))
            if stls:
                f.write(f"### 📂 {folder.name}\n\n")
                f.write("| Structure | Pièce | Lien | Chemin |\n")
                f.write("| :--- | :--- | :---: | :--- |\n")
                
                # Parcours récursif pour l'affichage multi-niveau
                for path in sorted(folder.rglob("*")):
                    if path.suffix.lower() == ".stl":
                        # Calcul de la profondeur pour l'indentation
                        depth = len(path.relative_to(folder).parts) - 1
                        indent = "  " * depth + "┗ " if depth > 0 else ""
                        
                        rel_path = path.relative_to(root_dir)
                        url_path = urllib.parse.quote(str(rel_path))
                        
                        f.write(f"| {indent}📄 | {path.stem} | [👁️ Voir]({url_path}) | `{rel_path}` |\n")
                f.write("\n")

        # --- SECTION 2 : Vue Arborescente Globale ---
        f.write("## 🗂️ Arborescence Complète du Projet\n\n")
        f.write("| Hiérarchie | Type | Lien |\n")
        f.write("| :--- | :---: | :--- |\n")
        
        # On parcourt tout le dépôt
        all_paths = sorted(list(root_dir.rglob("*")))
        for path in all_paths:
            # Ignorer les fichiers non STL et les dossiers exclus
            if any(ex in path.parts for ex in exclude): continue
            if path.is_dir() or path.suffix.lower() == ".stl":
                depth = len(path.parts)
                indent = "&nbsp;&nbsp;" * (depth - 1) + "📂 " if path.is_dir() else "&nbsp;&nbsp;" * (depth - 1) + "📄 "
                
                name = f"**{path.name}**" if path.is_dir() else path.name
                link = f"[Voir]({urllib.parse.quote(str(path))})" if path.is_suffix == ".stl" or not path.is_dir() else "-"
                
                if path.suffix.lower() == ".stl" or path.is_dir():
                    url_path = urllib.parse.quote(str(path.relative_to(root_dir)))
                    link = f"[🔗]({url_path})" if path.suffix.lower() == ".stl" else ""
                    f.write(f"| {indent}{name} | {'Dossier' if path.is_dir() else 'STL'} | {link} |\n")

    print(f"✅ BOM multi-niveaux généré dans '{output_file}'")

if __name__ == "__main__":
    generate_bom()
