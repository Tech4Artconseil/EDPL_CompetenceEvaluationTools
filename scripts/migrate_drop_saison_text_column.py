"""
migrate_drop_saison_text_column.py
------------------------------------
Migration : supprime la colonne texte `Saison` de la table `evaluats`.
La saison est désormais gérée exclusivement via `Saison_Id` (FK vers `saisons`).

Requiert SQLite >= 3.35.0 (ALTER TABLE DROP COLUMN).

Utilisation :
    python scripts/migrate_drop_saison_text_column.py
"""

import sqlite3
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(SCRIPT_DIR)
DB_PATH = os.path.join(PACKAGE_DIR, 'instance', 'evaluat.db')

if not os.path.exists(DB_PATH):
    print(f'Base de données introuvable : {DB_PATH}')
    sys.exit(1)

print(f'Base de données : {DB_PATH}')
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Vérifier la version SQLite
sqlite_ver = sqlite3.sqlite_version_info
print(f'Version SQLite : {sqlite3.sqlite_version}')
if sqlite_ver < (3, 35, 0):
    print('ERREUR : SQLite >= 3.35.0 requis pour DROP COLUMN.')
    print('Mise à jour SQLite ou migration manuelle nécessaire.')
    conn.close()
    sys.exit(1)

# Vérifier si la colonne Saison existe encore
existing_cols = [row[1] for row in cursor.execute('PRAGMA table_info(evaluats)').fetchall()]
if 'Saison' not in existing_cols:
    print("Colonne 'Saison' déjà absente — aucune modification.")
    conn.close()
    sys.exit(0)

# Vérifier que Saison_Id est bien présent (prérequis)
if 'Saison_Id' not in existing_cols:
    print("ERREUR : Colonne 'Saison_Id' absente. Exécutez d'abord migrate_add_saison_table.py")
    conn.close()
    sys.exit(1)

# Supprimer la colonne texte Saison
cursor.execute('ALTER TABLE evaluats DROP COLUMN Saison')
conn.commit()
print("Colonne 'Saison' supprimée de la table 'evaluats'.")

# Vérification finale
remaining = [row[1] for row in cursor.execute('PRAGMA table_info(evaluats)').fetchall()]
print(f'Colonnes restantes dans evaluats : {remaining}')
assert 'Saison' not in remaining, 'Échec : la colonne est encore présente!'
assert 'Saison_Id' in remaining, 'Échec : Saison_Id introuvable!'

conn.close()
print('Migration terminée avec succès.')
