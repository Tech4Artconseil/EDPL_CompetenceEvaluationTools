#!/usr/bin/env python3
"""
create_evaluat_notes_table.py

Backup DB and create `evaluat_notes` table if it doesn't exist.
"""
import os
import shutil
import sqlite3
import time
import sys


def find_db_path():
    script_dir = os.path.abspath(os.path.dirname(__file__))
    candidate = os.path.normpath(os.path.join(script_dir, '..', 'instance', 'evaluat.db'))
    if os.path.exists(candidate):
        return candidate
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


def table_exists(conn, table):
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table,))
    return cur.fetchone() is not None


def create_table(conn):
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS evaluat_notes (
            Id INTEGER PRIMARY KEY,
            Evaluat_Id INTEGER NOT NULL,
            Studnt_Id INTEGER NOT NULL,
            Note_Id INTEGER NOT NULL
        );
    ''')
    conn.commit()


def main():
    db_path = find_db_path()
    if not db_path:
        print('Database not found')
        sys.exit(1)
    print('Using database:', db_path)
    bak = backup_db(db_path)
    print('Backup created at', bak)
    conn = sqlite3.connect(db_path)
    if table_exists(conn, 'evaluat_notes'):
        print('Table evaluat_notes already exists; nothing to do')
        conn.close()
        return
    print('Creating evaluat_notes table...')
    create_table(conn)
    print('Done')
    conn.close()


if __name__ == '__main__':
    main()
