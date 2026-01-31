"""Migration script to add mapping_types table and MappingType_Id column to sheet_mappings.

Run from project root:
python scripts/migrate_mapping_types.py
"""
import os
import sqlite3
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'instance', 'evaluat.db')

if not os.path.exists(DB_PATH):
    print(f"Database not found at {DB_PATH}")
    raise SystemExit(1)

bak = DB_PATH + '.bak'
shutil.copyfile(DB_PATH, bak)
print(f"Backup created: {bak}")

con = sqlite3.connect(DB_PATH)
cur = con.cursor()

# Create mapping_types table if missing
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mapping_types'")
if not cur.fetchone():
    print('Creating table mapping_types...')
    cur.execute('''
        CREATE TABLE mapping_types (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Name TEXT NOT NULL,
            Description TEXT
        )
    ''')
    con.commit()
    print('mapping_types created.')
else:
    print('mapping_types already exists.')

# Check if sheet_mappings has MappingType_Id
cur.execute("PRAGMA table_info(sheet_mappings)")
cols = [r[1] for r in cur.fetchall()]
if 'MappingType_Id' not in cols or 'Evaluat_Id' in cols and any(r[1]=='Evaluat_Id' and r[3]==1 for r in cur.execute("PRAGMA table_info(sheet_mappings)").fetchall()):
    print('Altering sheet_mappings to add MappingType_Id and make Evaluat_Id nullable (recreate table)...')
    # read existing data
    cur.execute('SELECT Id, Evaluat_Id, Source_Table, Source_Column, Source_Filter, Target_Sheet, Target_Cell FROM sheet_mappings')
    rows = cur.fetchall()
    # drop old table
    cur.execute('DROP TABLE IF EXISTS sheet_mappings')
    # create new table with Evaluat_Id nullable and MappingType_Id
    cur.execute('''
        CREATE TABLE sheet_mappings (
            Id INTEGER PRIMARY KEY AUTOINCREMENT,
            Evaluat_Id INTEGER,
            MappingType_Id INTEGER,
            Source_Table TEXT NOT NULL,
            Source_Column TEXT NOT NULL,
            Source_Filter TEXT,
            Target_Sheet TEXT NOT NULL,
            Target_Cell TEXT NOT NULL,
            FOREIGN KEY(Evaluat_Id) REFERENCES evaluats(Id),
            FOREIGN KEY(MappingType_Id) REFERENCES mapping_types(Id)
        )
    ''')
    # insert back old rows (with MappingType_Id NULL)
    for r in rows:
        cur.execute('INSERT INTO sheet_mappings (Id, Evaluat_Id, Source_Table, Source_Column, Source_Filter, Target_Sheet, Target_Cell) VALUES (?,?,?,?,?,?,?)', r)
    con.commit()
    print('sheet_mappings recreated and data migrated.')
else:
    print('sheet_mappings already up-to-date.')

con.close()
print('Migration completed.')
