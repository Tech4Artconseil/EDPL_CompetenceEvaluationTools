"""
Migration script to introduce `skill_sets` table and convert existing
string `SkillSet_Id` values in `skills` and `evaluats` into integer
foreign keys referencing `skill_sets.Id`.

Usage:
    python scripts/migrate_skillsets.py

What it does:
 - makes a timestamped backup of instance/evaluat.db
 - creates `skill_sets` and populates it from distinct values found in
   `skills.SkillSet_Id` (inserting a placeholder for NULL values)
 - creates new `skills` and `evaluats` tables with `SkillSet_Id` as INTEGER FK
 - copies data mapping old SkillSet names -> new skill_sets.Id
 - preserves other columns

Please review the script before running and keep backups.
"""
import sqlite3
import os
import shutil
import time

HERE = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(HERE, 'instance', 'evaluat.db')

if not os.path.exists(DB_PATH):
    print(f"Database not found: {DB_PATH}")
    raise SystemExit(1)

# Backup
ts = time.strftime('%Y%m%d%H%M%S')
backup = DB_PATH + f'.bak.{ts}'
shutil.copy2(DB_PATH, backup)
print(f"Backup created: {backup}")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

try:
    c.execute('PRAGMA foreign_keys=OFF')
    conn.commit()

    # Create skill_sets table
    c.execute('''
    CREATE TABLE IF NOT EXISTS skill_sets (
        Id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT NOT NULL UNIQUE
    )
    ''')
    conn.commit()

    # gather distinct SkillSet names from skills (old string column)
    c.execute("SELECT DISTINCT SkillSet_Id FROM skills")
    rows = c.fetchall()
    mapping = {}
    for r in rows:
        name = r['SkillSet_Id']
        if name is None:
            name = '__unknown__'
        # insert or ignore, then get id
        c.execute('INSERT OR IGNORE INTO skill_sets(Name) VALUES(?)', (name,))
    conn.commit()

    # build mapping name -> id
    c.execute('SELECT Id, Name FROM skill_sets')
    for r in c.fetchall():
        mapping[r['Name']] = r['Id']

    print(f"Found and registered skill_sets: {len(mapping)}")

    # Create new skills table with integer FK SkillSet_Id
    c.execute('''
    CREATE TABLE skills_new (
        Id INTEGER PRIMARY KEY,
        SkillSet_Id INTEGER NOT NULL,
        Code TEXT NOT NULL,
        Descrip TEXT NOT NULL,
        FOREIGN KEY(SkillSet_Id) REFERENCES skill_sets(Id)
    )
    ''')

    # Copy skills -> skills_new mapping SkillSet name to id
    c.execute('SELECT Id, SkillSet_Id, Code, Descrip FROM skills')
    skills = c.fetchall()
    for s in skills:
        name = s['SkillSet_Id'] if s['SkillSet_Id'] is not None else '__unknown__'
        ssid = mapping.get(name)
        if ssid is None:
            # insert and refresh mapping
            c.execute('INSERT INTO skill_sets(Name) VALUES(?)', (name,))
            ssid = c.lastrowid
            mapping[name] = ssid
        c.execute('INSERT INTO skills_new(Id, SkillSet_Id, Code, Descrip) VALUES(?,?,?,?)', (s['Id'], ssid, s['Code'], s['Descrip']))
    conn.commit()

    # Create new evaluats table with integer FK SkillSet_Id
    # We need to preserve other columns: Id, Name, Group_Id, Show_Optional_Column, CreatedAt, Sheet_Local_Path
    c.execute('''
    CREATE TABLE evaluats_new (
        Id INTEGER PRIMARY KEY,
        Name TEXT NOT NULL,
        Group_Id INTEGER NOT NULL,
        SkillSet_Id INTEGER NOT NULL,
        Show_Optional_Column INTEGER NOT NULL DEFAULT 0,
        CreatedAt TEXT,
        Sheet_Local_Path TEXT,
        FOREIGN KEY(Group_Id) REFERENCES studnt_grps(Id),
        FOREIGN KEY(SkillSet_Id) REFERENCES skill_sets(Id)
    )
    ''')

    c.execute('SELECT Id, Name, Group_Id, SkillSet_Id, Show_Optional_Column, CreatedAt, Sheet_Local_Path FROM evaluats')
    evals = c.fetchall()
    for e in evals:
        name = e['SkillSet_Id'] if e['SkillSet_Id'] is not None else '__unknown__'
        ssid = mapping.get(name)
        if ssid is None:
            c.execute('INSERT INTO skill_sets(Name) VALUES(?)', (name,))
            ssid = c.lastrowid
            mapping[name] = ssid
        # SQLite stores booleans as integers
        so = e['Show_Optional_Column'] if e['Show_Optional_Column'] is not None else 0
        c.execute('INSERT INTO evaluats_new(Id, Name, Group_Id, SkillSet_Id, Show_Optional_Column, CreatedAt, Sheet_Local_Path) VALUES(?,?,?,?,?,?,?)', (e['Id'], e['Name'], e['Group_Id'], ssid, so, e['CreatedAt'], e['Sheet_Local_Path']))
    conn.commit()

    # Rename old tables and replace with new
    c.execute('ALTER TABLE skills RENAME TO skills_old')
    c.execute('ALTER TABLE skills_new RENAME TO skills')
    c.execute('ALTER TABLE evaluats RENAME TO evaluats_old')
    c.execute('ALTER TABLE evaluats_new RENAME TO evaluats')
    conn.commit()

    print('Migration complete. Old tables renamed to *_old. Please verify and drop them when satisfied.')

finally:
    c.execute('PRAGMA foreign_keys=ON')
    conn.commit()
    conn.close()

print('Done.')
