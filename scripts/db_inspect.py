import sqlite3, os
p = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'evaluat.db')
print('DB:', p)
if not os.path.exists(p):
    print('MISSING')
    raise SystemExit(1)
con = sqlite3.connect(p)
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('tables:')
for r in cur.fetchall():
    print(' -', r[0])
for t in ('mapping_types', 'sheet_mappings'):
    print('\nPRAGMA table_info(%s):' % t)
    try:
        cur.execute(f"PRAGMA table_info({t})")
        for r in cur.fetchall():
            print('   ', r)
    except Exception as e:
        print('   error:', e)
con.close()
