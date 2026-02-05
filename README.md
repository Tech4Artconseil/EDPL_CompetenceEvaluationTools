# Student Competence Evaluation Tool

A Flask-based web application for evaluating students based on competencies and skill levels. This tool helps workflow consultants assess student performance across multiple skills using a color-coded grid system.

## Features

- **Interactive Grid View**: Students (rows) vs Skills (columns) grid layout
- **Level Selection**: Four-level evaluation system with color coding:
  - 🔴 Red (20%) - Maitrise insufisente
  - 🟡 Yellow (50%) - maitrise Faible
  - 🟢 Green (75%) - Maitrise sufisante
  - 🔵 Blue (100%) - Tres bonne maitrise
- **Comment System**: Add and view comments for each student/skill combination
- **CSV Export**: Export evaluation results with semicolon separator
- **Real-time Updates**: AJAX-based score updates without page refresh

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Tech4Artconseil/EDPL_CompetenceEvaluationTools.git
cd EDPL_CompetenceEvaluationTools
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database with sample data:
```bash
python Data_Init.py
```

This will create:
- Level Set #1 with 4 evaluation levels
- Skills Set #1 (DNMADE3_18.3) with 3 skills
- Student Group #1 (DNMADE3_INT_IP_A) with 7 students (Étudiant 17-23)
- Evaluation #1: "Rhino Modeling Pince Alors _SwabDesign_"

## Running the Application

Start the Flask development server:
```bash
python App_Main.py
```

The application will be available at: `http://localhost:5000`

## Usage

### Evaluating Students

1. Open the dashboard in your web browser
2. For each student/skill combination:
   - Select a level from the dropdown menu
   - The cell will automatically color-code based on the level
   - Changes are saved automatically to the database

### Adding Comments

1. Click the 💬 button in any cell
2. A modal will open showing existing comments
3. Type your comment in the text area
4. Click "Add Comment" to save
5. The comment count will appear next to the 💬 button

### Exporting Data

Click the "Export CSV" button to download evaluation results as a CSV file with semicolon separators.

### Photos des étudiants

- **Champ en base** : les URL des photos sont stockées dans le champ `Photo_Url` de la table `studnts`.
- **Convention de nommage** : l'application génère des candidats d'URL selon la règle "initiale du prénom + nom" normalisés (minuscules, sans accents ni caractères spéciales). Exemple : "Masa BAKIR" → `mbakir.jpg` (URL complète : `https://neocampus.lecolededesign.com/uploads/trombi/mbakir.jpg`).
- **Scripts disponibles** :
  - `scripts/fill_photo_urls_backup.py` : crée une sauvegarde de la base (`instance/evaluat.db.bak.<ts>`) puis remplit `Photo_Url` en masse (par défaut n'écrase pas les valeurs existantes ; utiliser `--force` pour forcer l'écrasement).
  - `scripts/import_students_from_names.py` : importer des étudiants depuis un CSV (`Name`, optionnel `Email`, `Group`) et générer `Photo_Url` (option `--verify` pour vérifier l'existence distante).
  - `image_fetcher.py` : utilitaires de normalisation / génération de candidats et vérification HTTP.
- **Comportement UI** : si l'image est absente ou si le chargement renvoie une erreur, l'interface affiche un cercle gris (placeholder) et cache le nom de l'étudiant dans la grille pour éviter l'affichage d'un texte alternatif. Ceci est géré côté CSS/JS pour préserver la mise en page.
- **Respect & sécurité** : avant d'utiliser les scripts de collecte, vérifiez les conditions d'utilisation du site et la conformité RGPD / vie privée. Utilisez un compte autorisé ou une API si disponible.

## Project Structure

```
EDPL_CompetenceEvaluationTools/
├── App_Main.py              # Flask application with routes and logic
├── Data_Models.py           # SQLAlchemy database models
├── Data_Init.py            # Database initialization script
├── requirements.txt         # Python dependencies
├── templates/
│   └── Eval_Dash.html      # Main dashboard template
├── static/
│   └── css/
│       └── Main_Style.css  # Application styling
└── instance/
    └── evaluat.db          # SQLite database (created on first run)
```

## Database Schema

# Student Competence Evaluation Tool

Application web (Flask) pour évaluer des étudiants selon des compétences et des niveaux.
Ce dépôt fournit : interface de saisie, API AJAX, import/export CSV/XLSX, gestion admin et outils de remplissage de modèles Excel.

## Fonctionnalités principales

- Tableau de bord interactif : étudiants (lignes) × compétences (colonnes) avec sélection de niveau
- Système de niveaux (ex. 20 / 50 / 75 / 100) avec couleur associée et description
- Gestion des commentaires par étudiant / compétence (API pour lister/ajouter)
- Gestion de `Note` (valeurs numériques) et affectation par étudiant pour une colonne optionnelle
- Import d'étudiants et de compétences : CSV (aperçu + confirmation), extraction depuis HTML ou URL (heuristiques de matching noms/images/emails)
- Administration CRUD (ressources : skills, studnts, evaluats, levels, notes, mapping_types, sheet_mappings)
- Remplissage de templates XLSX et génération de feuilles par étudiant (dry-run disponible) via `sheets_local.py`
- Export CSV (séparateur `;`) et export XLSX coloré (nécessite `openpyxl`)
- Scripts utilitaires dans `scripts/` (migrations, contrôles, etc.)

## Installation

### Prérequis

- Python 3.8+
- pip

Certaines fonctionnalités optionnelles nécessitent :
- `openpyxl` (export/fill XLSX)
- `beautifulsoup4` (import depuis HTML)
- `requests` (import depuis URL)

Installer dépendances :

```bash
pip install -r requirements.txt
```

## Initialisation des données

Pour prépeupler la base :

```bash
python Data_Init.py
```

Le script crée un jeu d'exemple (niveaux, compétences, groupe d'étudiants, évaluation et lignes `Score`).
Si la base existe déjà, le script ne dupliquera pas les données.

Pour réinitialiser manuellement : supprimer `instance/evaluat.db` puis relancer `Data_Init.py`.

## Lancer l'application

```bash
python App_Main.py
```

Par défaut : http://localhost:5000

## Usage (résumé)

- Évaluer : sélectionner un niveau dans la cellule — sauvegarde via AJAX
- Commenter : ouvrir le modal depuis la cellule et ajouter un texte
- Exporter : `Export CSV` (séparateur `;`) ou `Export XLSX` (couleurs requièrent `openpyxl`)
- Importer : via l'admin → Import (CSV / HTML / URL) — utiliser l'aperçu puis confirmer l'import
- Remplir templates XLSX : depuis l'admin ou le tableau de bord, preview puis génération

## Structure du projet (fichiers importants)

```
EDPL_CompetenceEvaluationTools/
├── App_Main.py
├── admin.py
├── import_csv.py
├── Data_Init.py
├── Data_Models.py
├── sheets_local.py
├── requirements.txt
├── templates/
├── static/
├── scripts/
└── instance/ (evaluat.db et backups)
```

## Schéma de la base de données (modèles)

Les tables principales implémentées dans `Data_Models.py` :

- `Level` (niveaux, pourcentage, couleur, description)
- `Skill` (compétence : SkillSet_Id, Code, Descrip)
- `StudntGrp` (groupes d'étudiants)
 - `Studnt` (étudiants : Name, Email, Photo_Url, Group_Id)
- `Evaluat` (séances d'évaluation : Group_Id, SkillSet_Id, Sheet_Local_Path...)
- `Score` (ligne par étudiant × compétence pour une évaluation)
- `Comment` (commentaires)
- `Note` (valeurs numériques utilisables pour une colonne optionnelle)
- `EvaluatNote` (association Note ↔ étudiant pour une évaluation)
- `SheetMapping` / `MappingType` (mappings réutilisables pour remplissage XLSX)

Remarque importante : le code client/serveur gère des commentaires pouvant être liés uniquement à un étudiant (sans `Skill_Id`), mais le modèle `Comment` dans `Data_Models.py` déclare `Skill_Id` comme `nullable=False`. Il existe donc une incohérence potentielle entre le modèle et certains usages du code — vérifier/adapter `Comment.Skill_Id` si vous souhaitez autoriser des commentaires « généraux » par étudiant.

## Dépendances optionnelles

- `openpyxl` : export et remplissage XLSX
- `beautifulsoup4` : import depuis HTML
- `requests` : import depuis URL

Ces paquets figurent dans `requirements.txt` mais peuvent être facultatifs selon l'usage.

## Scripts utiles

- `check_db.py` : affichage des tables SQLite
- `check_evaluat_scores.py` : vérifie que le nombre d'entrées `scores` correspond à `students × skills` pour une évaluation
- `scripts/` : migrations et outils d'administration supplémentaires

## Conventions de nommage

Le code contient quelques conventions (variables et noms abrégés), mais elles ne sont pas appliquées de façon strictement homogène dans tout le projet. Le README ne présente donc plus de règles très contraignantes ; se référer au code pour les cas concrets.

## Licence

GNU GENERAL PUBLIC LICENSE — voir le fichier `LICENSE`.

## Support

Ouvrez une issue sur le dépôt pour signaler un bug ou demander une fonctionnalité.

---

Si vous voulez, je peux :
- corriger `Data_Models.py` pour autoriser `Comment.Skill_Id = NULL` (ou)
- modifier le code pour toujours fournir une valeur `Skill_Id` aux commentaires.
Dites-moi quelle option vous préférez et j'appliquerai le changement.
