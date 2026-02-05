"""
Add `Photo_Url` column to `studnts` table if it does not exist.
Run from repository root (same Python environment as the app):
    python scripts/migrate_add_photo_url.py
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'evaluat.db')

if not os.path.exists(DB_PATH):
    print(f"Database not found: {DB_PATH}")
    raise SystemExit(1)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
try:
    cur.execute("PRAGMA table_info(studnts)")
    cols = [r[1] for r in cur.fetchall()]
    if 'Photo_Url' in cols:
        print('Column Photo_Url already exists; nothing to do.')
    else:
        print('Adding column Photo_Url to studnts...')
        cur.execute('ALTER TABLE studnts ADD COLUMN Photo_Url TEXT')
        conn.commit()
        print('Column added successfully.')
finally:
    cur.close()
    conn.close()
