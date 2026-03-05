"""
create_seed_db.py
=================
Génère une base SQLite de démo (seed) à distribuer avec le build.

La BDD contient les données minimales fonctionnelles :
  - 4 niveaux (levels)
  - 21 notes (0-20)
  - 2 SkillSets + compétences associées
  - 1 saison "Test"
  - 1 groupe test avec 3 étudiants fictifs
  - 1 évaluation test (grille pré-remplie avec quelques scores de démo)

Usage (depuis la racine du projet) :
    python BUILDING/create_seed_db.py [OUTPUT_DB_PATH]

Par défaut, génère : BUILDING/seed_instance/evaluat.db
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Chemin de sortie
# ---------------------------------------------------------------------------
DEFAULT_OUTPUT = os.path.join(os.path.dirname(__file__), 'seed_instance', 'evaluat.db')
OUTPUT_PATH = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# Supprimer l'éventuelle db précédente pour repartir proprement
if os.path.exists(OUTPUT_PATH):
    os.remove(OUTPUT_PATH)

print(f'→ Génération de la BDD seed : {OUTPUT_PATH}')

conn = sqlite3.connect(OUTPUT_PATH)
cur = conn.cursor()

# ---------------------------------------------------------------------------
# Schéma (doit correspondre exactement à Data_Models.py)
# ---------------------------------------------------------------------------
SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS saisons (
    "Id"      INTEGER PRIMARY KEY AUTOINCREMENT,
    "Name"    VARCHAR(50)  NOT NULL UNIQUE,
    "Descrip" VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS levels (
    "Id"         INTEGER PRIMARY KEY AUTOINCREMENT,
    "LevelSet_Id" INTEGER NOT NULL,
    "Percent"    INTEGER NOT NULL,
    "Descrip"    VARCHAR(100) NOT NULL,
    "Color"      VARCHAR(20)  NOT NULL
);

CREATE TABLE IF NOT EXISTS skill_sets (
    "Id"   INTEGER PRIMARY KEY AUTOINCREMENT,
    "Name" VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS skills (
    "Id"          INTEGER PRIMARY KEY AUTOINCREMENT,
    "SkillSet_Id" INTEGER NOT NULL REFERENCES skill_sets("Id"),
    "Code"        VARCHAR(20)  NOT NULL,
    "Descrip"     VARCHAR(200) NOT NULL
);

CREATE TABLE IF NOT EXISTS studnt_grps (
    "Id"   INTEGER PRIMARY KEY AUTOINCREMENT,
    "Name" VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS studnts (
    "Id"        INTEGER PRIMARY KEY AUTOINCREMENT,
    "Name"      VARCHAR(100) NOT NULL,
    "Email"     VARCHAR(100) NOT NULL,
    "Photo_Url" VARCHAR(400),
    "Group_Id"  INTEGER NOT NULL REFERENCES studnt_grps("Id")
);

CREATE TABLE IF NOT EXISTS mapping_types (
    "Id"          INTEGER PRIMARY KEY AUTOINCREMENT,
    "Name"        VARCHAR(200) NOT NULL,
    "Description" TEXT
);

CREATE TABLE IF NOT EXISTS evaluats (
    "Id"                   INTEGER PRIMARY KEY AUTOINCREMENT,
    "Name"                 VARCHAR(200) NOT NULL,
    "Group_Id"             INTEGER NOT NULL REFERENCES studnt_grps("Id"),
    "SkillSet_Id"          INTEGER NOT NULL REFERENCES skill_sets("Id"),
    "Show_Optional_Column" BOOLEAN NOT NULL DEFAULT 0,
    "CreatedAt"            DATETIME DEFAULT CURRENT_TIMESTAMP,
    "Sheet_Local_Path"     VARCHAR(400),
    "Saison_Id"            INTEGER REFERENCES saisons("Id")
);

CREATE TABLE IF NOT EXISTS sheet_mappings (
    "Id"             INTEGER PRIMARY KEY AUTOINCREMENT,
    "Evaluat_Id"     INTEGER REFERENCES evaluats("Id"),
    "MappingType_Id" INTEGER REFERENCES mapping_types("Id"),
    "Source_Table"   VARCHAR(50)  NOT NULL,
    "Source_Column"  VARCHAR(100) NOT NULL,
    "Source_Filter"  VARCHAR(200),
    "Target_Sheet"   VARCHAR(100) NOT NULL,
    "Target_Cell"    VARCHAR(20)  NOT NULL
);

CREATE TABLE IF NOT EXISTS scores (
    "Id"        INTEGER PRIMARY KEY AUTOINCREMENT,
    "Evaluat_Id" INTEGER NOT NULL REFERENCES evaluats("Id"),
    "Studnt_Id"  INTEGER NOT NULL REFERENCES studnts("Id"),
    "Skill_Id"   INTEGER         REFERENCES skills("Id"),
    "Level_Id"   INTEGER         REFERENCES levels("Id")
);

CREATE TABLE IF NOT EXISTS comments (
    "Id"         INTEGER PRIMARY KEY AUTOINCREMENT,
    "Evaluat_Id" INTEGER NOT NULL REFERENCES evaluats("Id"),
    "Studnt_Id"  INTEGER NOT NULL REFERENCES studnts("Id"),
    "Skill_Id"   INTEGER         REFERENCES skills("Id"),
    "Text"       TEXT    NOT NULL,
    "CreatedAt"  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notes (
    "Id"       INTEGER PRIMARY KEY AUTOINCREMENT,
    "Valeure"  BIGINT  NOT NULL,
    "Descript" TEXT
);

CREATE TABLE IF NOT EXISTS evaluat_notes (
    "Id"         INTEGER PRIMARY KEY AUTOINCREMENT,
    "Evaluat_Id" INTEGER NOT NULL REFERENCES evaluats("Id"),
    "Studnt_Id"  INTEGER NOT NULL REFERENCES studnts("Id"),
    "Note_Id"    INTEGER NOT NULL REFERENCES notes("Id")
);

CREATE TABLE IF NOT EXISTS evaluat_grps (
    "Id"         INTEGER PRIMARY KEY AUTOINCREMENT,
    "Name"       VARCHAR(100) NOT NULL,
    "Evaluat_Id" INTEGER NOT NULL REFERENCES evaluats("Id"),
    "CreatedAt"  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evaluat_grp_members (
    "Id"            INTEGER PRIMARY KEY AUTOINCREMENT,
    "EvaluatGrp_Id" INTEGER NOT NULL REFERENCES evaluat_grps("Id"),
    "Studnt_Id"     INTEGER NOT NULL REFERENCES studnts("Id")
);
"""

for stmt in SCHEMA_SQL.split(';'):
    stmt = stmt.strip()
    if stmt:
        cur.execute(stmt)
conn.commit()
print('  ✔ Schéma créé')

# ---------------------------------------------------------------------------
# 1. Levels — 4 niveaux (LevelSet_Id=1)
# ---------------------------------------------------------------------------
_LEVELS = [
    (1, 20,  'MI',  '#ff0000'),
    (1, 50,  'MF',  '#ffb300'),
    (1, 75,  'MS',  '#1cd301'),
    (1, 100, 'TBM', '#005500'),
]
cur.executemany(
    'INSERT INTO levels (LevelSet_Id, Percent, Descrip, Color) VALUES (?,?,?,?)',
    _LEVELS
)
print(f'  ✔ {len(_LEVELS)} niveaux insérés')

# ---------------------------------------------------------------------------
# 2. Notes — échelle 0-20
# ---------------------------------------------------------------------------
_NOTES_DESCRIP = {
    0:  'Non évalué ou travail non rendu',
    1:  'Maîtrise insuffisante',
    2:  'Maîtrise insuffisante',
    3:  'Maîtrise insuffisante',
    4:  'Maîtrise faible',
    5:  'Maîtrise faible',
    6:  'Maîtrise faible',
    7:  'Maîtrise suffisante',
    8:  'Maîtrise suffisante',
    9:  'Très bonne maîtrise',
    10: 'Très bonne maîtrise',
}
_NOTES = [(v, _NOTES_DESCRIP.get(v)) for v in range(21)]
cur.executemany('INSERT INTO notes (Valeure, Descript) VALUES (?,?)', _NOTES)
print(f'  ✔ {len(_NOTES)} notes insérées')

# ---------------------------------------------------------------------------
# 3. SkillSets + Skills
# ---------------------------------------------------------------------------
cur.execute("INSERT INTO skill_sets (Name) VALUES ('DNMADE3_18.3')")           # Id=1
cur.execute("INSERT INTO skill_sets (Name) VALUES ('CUSTM_Eval_Set_1')")        # Id=2

_SKILLS_SS1 = [
    (1, 'C1.1',  "Utiliser les outils numériques de référence et les règles de sécurité informatique pour acquérir, traiter, produire et diffuser de l'information ainsi que pour collaborer en interne et en externe."),
    (1, 'C4.4',  "Développer une argumentation avec un esprit critique"),
    (1, 'C6.2',  "S'informer des pratiques d'atelier et des productions émergentes associant ou non le numérique et la CFAO."),
    (1, 'C9.1',  "Faire état d'une écriture et d'une pratique expérimentale personnelle : des dimensions plastique, sensorielle, graphique, volumique, technologique, structurelle et signifiante de design de mode."),
    (1, 'C9.3',  "S'auto évaluer et se remettre en question pour apprendre : maîtrise des outils, protocoles et techniques de design de mode."),
    (1, 'C10.5', "Veiller au respect des échéances et au contrôle technique et artistique selon les règles du métier."),
    (1, 'C10.6', "Enoncer ses idées de design de mode, argumenter ses choix de conception et de création au travers de supports et de médias adaptés 2D et/ou 3D."),
    (1, 'C11.1', "Saisir les éléments caractéristiques d'un projet de design de mode au travers de dessins, maquettes et d'échantillons en prenant en compte les étapes de réalisation et production."),
    (1, 'C11.2', "Prototyper ou réaliser tout ou partie du projet en incluant les outils numériques CAO, DAO, PAO"),
]
_SKILLS_SS2 = [
    (2, 'Acid_A',   "Assiduité en cours et dans le travail personnel. Participe en cours et reste attentif. Montre de la curiosité."),
    (2, 'Experim_A',"Expérimente, teste et s'autocorrige. Montre une volonté de découvrir de nouvelles techniques."),
    (2, 'Partg_A',  "Partage ses connaissances, collabore avec ses pairs et reste ouvert à d'autres visions et techniques."),
    (2, 'Ponct_A',  "Est ponctuel, n'arrive pas en retard."),
]
cur.executemany('INSERT INTO skills (SkillSet_Id, Code, Descrip) VALUES (?,?,?)', _SKILLS_SS1)
cur.executemany('INSERT INTO skills (SkillSet_Id, Code, Descrip) VALUES (?,?,?)', _SKILLS_SS2)
print(f'  ✔ {len(_SKILLS_SS1)+len(_SKILLS_SS2)} compétences insérées (2 SkillSets)')

# ---------------------------------------------------------------------------
# 4. Saison test
# ---------------------------------------------------------------------------
cur.execute("INSERT INTO saisons (Name, Descrip) VALUES ('Test', 'Saison de démonstration')")
saison_id = cur.lastrowid   # = 1
print(f'  ✔ Saison "Test" insérée (Id={saison_id})')

# ---------------------------------------------------------------------------
# 5. Groupe et étudiants de démo
# ---------------------------------------------------------------------------
cur.execute("INSERT INTO studnt_grps (Name) VALUES ('Groupe_Demo')")
grp_id = cur.lastrowid   # = 1

_TROMBI = '/static/uploads/trombi/'
_STUDENTS = [
    ('DUPONT Alice',   'alice.dupont@demo.local',   _TROMBI + 'DUPONT_Alice.png'),
    ('MARTIN Thomas',  'thomas.martin@demo.local',  _TROMBI + 'MARTIN_Thomas.png'),
    ('BERNARD Léa',    'lea.bernard@demo.local',    _TROMBI + 'BERNARD_Lea.png'),
    ('MOREAU Julien',  'julien.moreau@demo.local',  _TROMBI + 'MOREAU_Julien.jpg'),
    ('PETIT Emma',     'emma.petit@demo.local',     _TROMBI + 'PETIT_Emma.jpg'),
]
for name, email, photo in _STUDENTS:
    cur.execute(
        'INSERT INTO studnts (Name, Email, Photo_Url, Group_Id) VALUES (?,?,?,?)',
        (name, email, photo, grp_id)
    )
student_ids = list(range(1, len(_STUDENTS) + 1))
print(f'  ✔ {len(_STUDENTS)} étudiants dans "Groupe_Demo"')

# ---------------------------------------------------------------------------
# 6. Évaluation de démo (SkillSet DNMADE3_18.3, Saison Test)
# ---------------------------------------------------------------------------
cur.execute("""
    INSERT INTO evaluats (Name, Group_Id, SkillSet_Id, Show_Optional_Column, CreatedAt, Sheet_Local_Path, Saison_Id)
    VALUES ('Demo_Evaluation', ?, 1, 1, ?, 'None', ?)
""", (grp_id, datetime.now(timezone.utc).isoformat(), saison_id))
evaluat_id = cur.lastrowid
print(f'  ✔ Évaluation "Demo_Evaluation" créée (Id={evaluat_id})')

# ---------------------------------------------------------------------------
# 7. Scores de démo (quelques niveaux pré-remplis pour illustrer le tableau)
# ---------------------------------------------------------------------------
# skill_ids pour SkillSet_Id=1 : 1 à 9
# level_ids : 1=MI, 2=MF, 3=MS, 4=TBM
_DEMO_LEVELS_CYCLE = [3, 4, 2, 3, 4, 3, 2, 4, 3]   # 9 compétences par étudiant
for s_idx, stud_id in enumerate(student_ids):
    for skill_idx, skill_id in enumerate(range(1, 10)):   # compétences 1-9
        # Alterner pour avoir un résultat visuellement varié
        lvl = _DEMO_LEVELS_CYCLE[(s_idx + skill_idx) % len(_DEMO_LEVELS_CYCLE)]
        cur.execute(
            'INSERT INTO scores (Evaluat_Id, Studnt_Id, Skill_Id, Level_Id) VALUES (?,?,?,?)',
            (evaluat_id, stud_id, skill_id, lvl)
        )
score_count = len(student_ids) * 9
print(f'  ✔ {score_count} scores de démo insérés')

conn.commit()
conn.close()
print(f'\n✅ BDD seed générée avec succès : {OUTPUT_PATH}')
