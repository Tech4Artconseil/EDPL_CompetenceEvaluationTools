"""
migrate_add_saison_table.py
----------------------------
Migration : création de la table `saisons` et ajout de la colonne `saison_id`
(FK nullable) sur la table `evaluats`.

Les saisons déjà présentes en texte libre (colonne `saison` d'`evaluats`) sont
automatiquement importées dans la nouvelle table, et la FK est mise à jour.

Utilisation :
    python scripts/migrate_add_saison_table.py
"""

import sqlite3
import os
import sys

# Chemin vers la base de données
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PACKAGE_DIR, 'instance', 'evaluat.db')

if not os.path.exists(DB_PATH):
    print(f'Base de données introuvable : {DB_PATH}')
    sys.exit(1)

print(f'Base de données : {DB_PATH}')
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# ── 1. Créer la table saisons si elle n'existe pas encore ───────────────────
cursor.execute("""
    CREATE TABLE IF NOT EXISTS saisons (
        Id      INTEGER PRIMARY KEY AUTOINCREMENT,
        Name    VARCHAR(50)  NOT NULL UNIQUE,
        Descrip VARCHAR(200) NULL
    )
""")
print('Table `saisons` : OK')

# ── 2. Ajouter la colonne saison_id sur evaluats si absente ─────────────────
existing_cols = [row[1] for row in cursor.execute('PRAGMA table_info(evaluats)').fetchall()]
if 'Saison_Id' not in existing_cols:
    cursor.execute('ALTER TABLE evaluats ADD COLUMN Saison_Id INTEGER REFERENCES saisons(Id)')
    print('Colonne `Saison_Id` ajoutée à `evaluats`')
else:
    print('Colonne `Saison_Id` déjà présente')

# ── 3. Importer les saisons texte existantes dans la table saisons ───────────
rows = cursor.execute(
    "SELECT DISTINCT Saison FROM evaluats WHERE Saison IS NOT NULL AND Saison != ''"
).fetchall()

imported = 0
for row in rows:
    name = row[0].strip()
    if not name:
        continue
    existing = cursor.execute('SELECT Id FROM saisons WHERE Name = ?', (name,)).fetchone()
    if not existing:
        cursor.execute('INSERT INTO saisons (Name) VALUES (?)', (name,))
        imported += 1
        print(f'  Saison importée : "{name}"')

if imported == 0:
    print('  (aucune nouvelle saison à importer)')
else:
    print(f'  {imported} saison(s) importée(s)')

# ── 4. Peupler Saison_Id sur les évaluations existantes ─────────────────────
updated = 0
evals = cursor.execute('SELECT Id, Saison FROM evaluats WHERE Saison IS NOT NULL').fetchall()
for ev in evals:
    ev_id = ev[0]
    saison_name = (ev[1] or '').strip()
    if not saison_name:
        continue
    sai = cursor.execute('SELECT Id FROM saisons WHERE Name = ?', (saison_name,)).fetchone()
    if sai:
        cursor.execute('UPDATE evaluats SET Saison_Id = ? WHERE Id = ?', (sai[0], ev_id))
        updated += 1

print(f'Évaluations mises à jour avec Saison_Id : {updated}')

conn.commit()
conn.close()
print('Migration terminée avec succès.')
