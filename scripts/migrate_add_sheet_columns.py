"""Migration script to add Sheet_Local_Path column to evaluats and create sheet_mappings table.

Run: python migrate_add_sheet_columns.py
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'evaluat.db')

if not os.path.exists(DB_PATH):
    print(f"Database not found at {DB_PATH}")
    raise SystemExit(1)

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

# Add column Sheet_Local_Path if missing
cur.execute("PRAGMA table_info(evaluats)")
cols = [r[1] for r in cur.fetchall()]
if 'Sheet_Local_Path' not in cols:
    print('Adding column Sheet_Local_Path to evaluats...')
    try:
        cur.execute("ALTER TABLE evaluats ADD COLUMN Sheet_Local_Path TEXT")
        con.commit()
        print('Column added.')
    except Exception as e:
        print('Failed to add column:', e)
else:
    print('Column Sheet_Local_Path already present.')

# Create sheet_mappings table if not exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sheet_mappings'")
if not cur.fetchone():
    print('Creating table sheet_mappings...')
    try:
        cur.execute('''
            CREATE TABLE sheet_mappings (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                Evaluat_Id INTEGER NOT NULL,
                Source_Table TEXT NOT NULL,
                Source_Column TEXT NOT NULL,
                Source_Filter TEXT,
                Target_Sheet TEXT NOT NULL,
                Target_Cell TEXT NOT NULL,
                FOREIGN KEY(Evaluat_Id) REFERENCES evaluats(Id)
            )
        ''')
        con.commit()
        print('Table created.')
    except Exception as e:
        print('Failed to create table:', e)
else:
    print('Table sheet_mappings already exists.')

con.close()
print('Migration completed.')
