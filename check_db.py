import os
import sqlite3

def check_db(path):
    print('checking:', path)
    if not os.path.exists(path):
        print('  missing')
        return
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    print('  tables:', tables)
    con.close()


if __name__ == '__main__':
    print('cwd:', os.getcwd())
    # check both possible locations
    check_db(os.path.join('instance', 'evaluat.db'))
    check_db('evaluat.db')
