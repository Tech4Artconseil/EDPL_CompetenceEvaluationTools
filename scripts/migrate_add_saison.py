"""
migrate_add_saison.py
Migration : ajoute la colonne `Saison` (TEXT, nullable) à la table `evaluats`.

Usage :
    python scripts/migrate_add_saison.py [--db <chemin/vers/evaluat.db>]

Par défaut, travaille sur instance/evaluat.db dans le dossier parent du script.
"""

import sqlite3
import os
import sys
import shutil
from datetime import datetime

# ── Chemin par défaut ────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(SCRIPT_DIR, '..', 'instance', 'evaluat.db')


def migrate(db_path: str) -> None:
    db_path = os.path.abspath(db_path)

    if not os.path.exists(db_path):
        print(f"[ERREUR] Base introuvable : {db_path}")
        sys.exit(1)

    # ── Sauvegarde préventive ───────────────────────────────────────────────
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_path = f"{db_path}.bak.{ts}"
    shutil.copy2(db_path, backup_path)
    print(f"[INFO] Sauvegarde créée : {backup_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # ── Vérifier si la colonne existe déjà ─────────────────────────────────
    cur.execute("PRAGMA table_info(evaluats)")
    columns = [row[1] for row in cur.fetchall()]

    if 'Saison' in columns:
        print("[INFO] La colonne 'Saison' existe déjà — aucune modification.")
        conn.close()
        return

    # ── Ajouter la colonne ──────────────────────────────────────────────────
    cur.execute("ALTER TABLE evaluats ADD COLUMN Saison TEXT")
    conn.commit()
    print("[OK] Colonne 'Saison' ajoutée à la table 'evaluats'.")

    # ── Afficher l'état courant ─────────────────────────────────────────────
    cur.execute("SELECT Id, Name, Saison FROM evaluats")
    rows = cur.fetchall()
    print(f"\n{'Id':>4}  {'Name':<40}  {'Saison'}")
    print("-" * 60)
    for r in rows:
        print(f"{r[0]:>4}  {str(r[1]):<40}  {r[2]}")

    conn.close()
    print("\n[INFO] Migration terminée. Renseignez 'Saison' via l'admin ou directement en base.")


if __name__ == '__main__':
    # Support optionnel de --db <chemin>
    db = DEFAULT_DB
    if '--db' in sys.argv:
        idx = sys.argv.index('--db')
        if idx + 1 < len(sys.argv):
            db = sys.argv[idx + 1]

    migrate(db)
