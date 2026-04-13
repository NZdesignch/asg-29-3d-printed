import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import argparse

# ============================================
# CONFIGURATION - À MODIFIER ICI UNE SEULE FOIS
# ============================================
REPO_URL = "https://github.com/NZdesignch/asg-29-3d-printed"  # ← URL du dépôt GitHub
OUTPUT_FILE = "bom.md"  # ← Nom du fichier de sortie (optionnel)
# ============================================

class STLAnalyzer:
    def __init__(self, repo_path: str):
        """
        Initialise l'analyseur STL.
        
        Args:
            repo_path: Chemin vers le dossier du dépôt GitHub
        """
        self.repo_path = Path(repo_path)
        self.stl_files = []
        self.nomenclature = {}
        
    def find_stl_files(self) -> List[Path]:
        """
        Trouve tous les fichiers .stl dans le dépôt.
        
        Returns:
            Liste des chemins des fichiers STL trouvés
        """
        stl_files = []
        # Recherche récursive de tous les fichiers .stl (insensible à la casse)
        for ext in ['*.stl', '*.STL']:
            stl_files.extend(self.repo_path.rglob(ext))
        
        self.stl_files = stl_files
        return stl_files
    
    def get_file_info(self, file_path: Path) -> Dict:
        """
        Récupère les informations d'un fichier STL.
        
        Args:
            file_path: Chemin du fichier STL
            
        Returns:
            Dictionnaire avec les informations du fichier
        """
        try:
            # Taille du fichier en octets
            size_bytes = file_path.stat().st_size
            
            # Convertir en taille lisible
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.2f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
            
            # Date de modification
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Chemin relatif
            rel_path = file_path.relative_to(self.repo_path)
            
            return {
                'name': file_path.name,
                'relative_path': rel_path,
                'size_bytes': size_bytes,
                'size_str': size_str,
                'modified': mod_time_str,
                'parent_dir': file_path.parent.relative_to(self.repo_path)
            }
        except Exception as e:
            print(f"Erreur lors de la lecture de {file_path}: {e}")
            return None
    
    def build_hierarchy(self) -> Dict:
        """
        Construit une hiérarchie multi-niveaux des fichiers STL.
        
        Returns:
            Dictionnaire représentant l'arborescence des fichiers
        """
        hierarchy = {}
        
        for stl_file in self.stl_files:
            info = self.get_file_info(stl_file)
            if info:
                # Décomposer le chemin en parties
                parts = list(info['relative_path'].parts)
                filename = parts.pop()  # Dernier élément = nom du fichier
                
                # Naviguer dans la hiérarchie
                current_level = hierarchy
                for part in parts:
                    if part not in current_level:
                        current_level[part] = {}
                    current_level = current_level[part]
                
                # Stocker les infos du fichier
                if 'files' not in current_level:
                    current_level['files'] = []
                current_level['files'].append(info)
        
        return hierarchy
    
    def generate_markdown(self, hierarchy: Dict, output_file: str = "nomenclature_stl.md"):
        """
        Génère le fichier Markdown avec la nomenclature.
        
        Args:
            hierarchy: Hiérarchie des fichiers
            output_file: Nom du fichier de sortie
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            # En-tête
            f.write("# Nomenclature des fichiers STL\n\n")
            f.write(f"**Dépôt analysé :** `{self.repo_path}`\n\n")
            f.write(f"**Date d'analyse :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Nombre total de fichiers STL :** {len(self.stl_files)}\n\n")
            
            if len(self.stl_files) == 0:
                f.write("⚠️ Aucun fichier STL trouvé dans ce dépôt.\n")
                return
            
            f.write("---\n\n")
            
            # Générer l'arborescence
            self._write_hierarchy(f, hierarchy)
            
            # Section récapitulative
            f.write("\n## 📊 Récapitulatif par dossier\n\n")
            
            # Compter les fichiers par dossier
            folder_stats = {}
            for stl_file in self.stl_files:
                info = self.get_file_info(stl_file)
                if info:
                    parent = str(info['parent_dir'])
                    if parent == '.':
                        parent = 'Racine'
                    folder_stats[parent] = folder_stats.get(parent, 0) + 1
            
            # Trier par nombre de fichiers (décroissant)
            for folder, count in sorted(folder_stats.items(), key=lambda x: x[1], reverse=True):
                f.write(f"- **{folder}** : {count} fichier(s)\n")
            
            # Liste complète des fichiers
            f.write("\n## 📋 Liste complète des fichiers\n\n")
            f.write("| # | Fichier | Chemin | Taille | Dernière modification |\n")
            f.write("|---|---------|--------|--------|---------------------|\n")
            
            for i, stl_file in enumerate(sorted(self.stl_files), 1):
                info = self.get_file_info(stl_file)
                if info:
                    f.write(f"| {i} | {info['name']} | `{info['relative_path']}` | {info['size_str']} | {info['modified']} |\n")
    
    def _write_hierarchy(self, f, hierarchy: Dict, indent_level: int = 0):
        """
        Écrit la hiérarchie dans le fichier Markdown (fonction récursive).
        
        Args:
            f: Objet fichier
            hierarchy: Dictionnaire de la hiérarchie
            indent_level: Niveau d'indentation actuel
        """
        # Trier les clés pour un affichage ordonné
        items = sorted(hierarchy.items())
        
        for key, value in items:
            if key == 'files':
                # Afficher les fichiers dans le dossier courant
                if value:
                    f.write("\n" + "  " * indent_level + "**Fichiers STL :**\n")
                    for file_info in sorted(value, key=lambda x: x['name']):
                        f.write("  " * (indent_level + 1) + f"- 📄 `{file_info['name']}`\n")
                        f.write("  " * (indent_level + 2) + f"  - Taille : {file_info['size_str']}\n")
                        f.write("  " * (indent_level + 2) + f"  - Modifié : {file_info['modified']}\n")
            else:
                # Afficher le dossier
                folder_icon = "📁"
                f.write("\n" + "  " * indent_level + f"{folder_icon} **{key}/**\n")
                # Appel récursif pour le contenu du dossier
                self._write_hierarchy(f, value, indent_level + 1)
    
    def analyze_and_export(self, output_file: str = "nomenclature_stl.md"):
        """
        Exécute l'analyse complète et exporte la nomenclature.
        
        Args:
            output_file: Nom du fichier de sortie
        """
        print(f"🔍 Recherche des fichiers STL dans {self.repo_path}...")
        stl_files = self.find_stl_files()
        
        if not stl_files:
            print("⚠️ Aucun fichier STL trouvé !")
        else:
            print(f"✅ {len(stl_files)} fichier(s) STL trouvé(s)")
            
        print("📊 Construction de la hiérarchie...")
        hierarchy = self.build_hierarchy()
        
        print(f"📝 Génération du fichier {output_file}...")
        self.generate_markdown(hierarchy, output_file)
        
        print(f"✅ Nomenclature générée avec succès dans {output_file}")
        return output_file

def clone_repository(repo_url: str, target_dir: str = None) -> str:
    """
    Clone un dépôt GitHub.
    
    Args:
        repo_url: URL du dépôt GitHub
        target_dir: Dossier cible pour le clonage (optionnel)
    
    Returns:
        Chemin du dossier cloné
    """
    if not target_dir:
        # Extraire le nom du dépôt de l'URL
        repo_name = repo_url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        target_dir = f"./{repo_name}"
    
    # Supprimer le dossier s'il existe déjà
    if os.path.exists(target_dir):
        print(f"📁 Le dossier {target_dir} existe déjà, suppression...")
        shutil.rmtree(target_dir)
    
    print(f"📥 Clonage du dépôt {repo_url}...")
    try:
        subprocess.run(['git', 'clone', repo_url, target_dir], check=True, capture_output=True, text=True)
        print(f"✅ Dépôt cloné avec succès dans {target_dir}")
        return target_dir
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du clonage : {e.stderr}")
        sys.exit(1)

def main():
    # Utilisation des variables globales
    global REPO_URL, OUTPUT_FILE
    
    # Vérifier si c'est une URL ou un chemin local
    if REPO_URL.startswith(('http://', 'https://', 'git@')):
        # C'est une URL, on clone d'abord
        print("🚀 Mode URL détecté - Clonage du dépôt...")
        repo_path = clone_repository(REPO_URL)
    else:
        # C'est un chemin local
        repo_path = REPO_URL
        if not os.path.exists(repo_path):
            print(f"❌ Erreur : Le chemin '{repo_path}' n'existe pas.")
            print("💡 Modifiez la variable REPO_URL en haut du script.")
            sys.exit(1)
    
    # Créer l'analyseur et exécuter
    analyzer = STLAnalyzer(repo_path)
    analyzer.analyze_and_export(OUTPUT_FILE)
    
    # Optionnel : supprimer le dépôt cloné après analyse
    # if REPO_URL.startswith(('http://', 'https://', 'git@')):
    #     print(f"🧹 Nettoyage - Suppression du dossier {repo_path}...")
    #     shutil.rmtree(repo_path)

if __name__ == "__main__":
    main()
