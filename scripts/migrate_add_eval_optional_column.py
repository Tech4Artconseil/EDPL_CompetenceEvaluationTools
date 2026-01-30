#!/usr/bin/env python3
"""
migrate_add_eval_optional_column.py

Backup the SQLite database and add the column Show_Optional_Column
to the `evaluats` table if it does not already exist.

Usage:
    python migrate_add_eval_optional_column.py
"""

import os
import shutil
import sqlite3
import time
import sys


def find_db_path():
    # Script lives in EDPL_CompetenceEvaluationTools/scripts
    script_dir = os.path.abspath(os.path.dirname(__file__))
    # instance folder is one level up from script_dir
    candidate = os.path.normpath(os.path.join(script_dir, '..', 'instance', 'evaluat.db'))
    if os.path.exists(candidate):
        return candidate
    # fallback to current working directory
    cwd_candidate = os.path.join(os.getcwd(), 'instance', 'evaluat.db')
    if os.path.exists(cwd_candidate):
        return cwd_candidate
    alt = os.path.join(os.getcwd(), 'evaluat.db')
    if os.path.exists(alt):
        return alt
    return None


def backup_db(db_path):
    dirname = os.path.dirname(db_path)
    ts = time.strftime('%Y%m%d_%H%M%S')
    bak_name = f'evaluat_backup_{ts}.db'
    bak_path = os.path.join(dirname, bak_name)
    shutil.copy2(db_path, bak_path)
    return bak_path


def column_exists(conn, table, column):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    cols = [r[1] for r in cur.fetchall()]
    return column in cols


def add_column(conn):
    cur = conn.cursor()
    # SQLite: add INTEGER column with default 0 (used as boolean)
    cur.execute("ALTER TABLE evaluats ADD COLUMN Show_Optional_Column INTEGER NOT NULL DEFAULT 0;")
    conn.commit()


def main():
    db_path = find_db_path()
    if not db_path:
        print('Database not found (looked for instance/evaluat.db and evaluat.db).')
        sys.exit(1)

    print('Using database:', db_path)

    try:
        bak = backup_db(db_path)
        print('Backup created at:', bak)
    except Exception as e:
        print('Failed to create backup:', e)
        sys.exit(1)

    try:
        conn = sqlite3.connect(db_path)
        if column_exists(conn, 'evaluats', 'Show_Optional_Column'):
            print('Column Show_Optional_Column already exists; nothing to do.')
            conn.close()
            # mark as done
            return

        print('Adding Show_Optional_Column to table evaluats...')
        add_column(conn)
        print('Column added successfully.')
        conn.close()
    except Exception as e:
        print('Error during migration:', e)
        print('Attempting to restore from backup...')
        try:
            shutil.copy2(bak, db_path)
            print('Database restored from backup.')
        except Exception as e2:
            print('Failed to restore backup:', e2)
        sys.exit(1)


if __name__ == '__main__':
    main()
