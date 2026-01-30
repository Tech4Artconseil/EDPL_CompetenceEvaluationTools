#!/usr/bin/env python3
"""
Create `notes` table in the SQLite DB if it does not exist.
This script:
- makes a timestamped backup of the DB
- connects to the DB and checks if the `notes` table exists
- if missing, creates it (Id INTEGER PRIMARY KEY, Valeure INTEGER NOT NULL, Descript TEXT)

Usage:
    python scripts/create_notes_table.py

Run from the project root (package folder) so the script finds `instance/evaluat.db`.
"""
import os
import shutil
import sqlite3
import sys
from datetime import datetime

PACKAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INSTANCE_DIR = os.path.join(PACKAGE_DIR, 'instance')
DB_PATH = os.path.join(INSTANCE_DIR, 'evaluat.db')

if not os.path.exists(DB_PATH):
    print('Database not found at', DB_PATH)
    sys.exit(1)

# Backup
ts = datetime.now().strftime('%Y%m%d%H%M%S')
backup_path = DB_PATH + f'.bak.{ts}'
print('Backing up', DB_PATH, '->', backup_path)
shutil.copy2(DB_PATH, backup_path)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

try:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notes';")
    if cur.fetchone():
        print('Table `notes` already exists — nothing to do.')
    else:
        print('Creating table `notes`...')
        cur.execute('''
            CREATE TABLE notes (
                Id INTEGER PRIMARY KEY,
                Valeure INTEGER NOT NULL,
                Descript TEXT
            );
        ''')
        conn.commit()
        print('Table `notes` created successfully.')
except Exception as e:
    print('Error:', e)
    conn.rollback()
    print('You can restore the DB from the backup at', backup_path)
finally:
    conn.close()

print('Done.')
