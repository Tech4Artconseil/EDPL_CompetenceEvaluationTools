#!/usr/bin/env python3
"""
Migration helper:
Make `comments.Skill_Id` nullable in the SQLite DB used by the app.

This script:
- creates a timestamped backup of the DB
- creates a new table `comments_new` with `Skill_Id` NULLABLE
- copies all rows from `comments` into `comments_new`
- drops the old `comments` table and renames `comments_new` -> `comments`

Run from the project package folder or simply:
python scripts/migrate_comments_skill_nullable.py

The script prints progress and will abort on error.
"""

import os
import shutil
import sqlite3
from datetime import datetime
import sys

# Locate DB like App_Main.py does
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
    print('Turning off foreign keys enforcement')
    cur.execute('PRAGMA foreign_keys=OFF;')

    # Create new table with Skill_Id nullable
    print('Creating new table comments_new')
    cur.execute('''
    CREATE TABLE comments_new (
        Id INTEGER PRIMARY KEY,
        Evaluat_Id INTEGER NOT NULL,
        Studnt_Id INTEGER NOT NULL,
        Skill_Id INTEGER,
        Text TEXT NOT NULL,
        CreatedAt DATETIME
    );
    ''')

    # Copy data
    print('Copying data from comments to comments_new')
    cur.execute('''
        INSERT INTO comments_new (Id, Evaluat_Id, Studnt_Id, Skill_Id, Text, CreatedAt)
        SELECT Id, Evaluat_Id, Studnt_Id, Skill_Id, Text, CreatedAt FROM comments;
    ''')

    # Drop old table
    print('Dropping old table comments')
    cur.execute('DROP TABLE comments;')

    # Rename
    print('Renaming comments_new -> comments')
    cur.execute('ALTER TABLE comments_new RENAME TO comments;')

    conn.commit()
    print('Migration completed successfully.')
    print('Re-enable foreign_keys')
    cur.execute('PRAGMA foreign_keys=ON;')
    conn.commit()
except Exception as e:
    print('Error during migration:', e)
    print('You can restore the DB from the backup at', backup_path)
    conn.rollback()
finally:
    conn.close()

print('Done.')
