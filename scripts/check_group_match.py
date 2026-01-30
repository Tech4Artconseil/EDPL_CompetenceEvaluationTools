#!/usr/bin/env python3
"""
Simple diagnostic: list groups in DB and test matching for a provided group name.
Usage:
    python scripts/check_group_match.py "DNMADE3_INT_RID_GR1_2526"
"""
import os, sys
from Data_Models import Db, StudntGrp
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import unicodedata

def normalize(s):
    if not s:
        return ''
    s = s.lower()
    s = unicodedata.normalize('NFKD', s)
    return ''.join(ch for ch in s if ch.isalnum())

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python scripts/check_group_match.py "GroupName"')
        sys.exit(1)
    target = sys.argv[1]
    # locate DB same as App_Main
    pkg = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    instance = os.path.join(pkg, 'instance')
    db_path = os.path.join(instance, 'evaluat.db')
    if not os.path.exists(db_path):
        print('DB not found at', db_path)
        sys.exit(1)
    engine = create_engine('sqlite:///' + db_path.replace('\\','/'))
    Session = sessionmaker(bind=engine)
    s = Session()
    groups = s.query(StudntGrp).all()
    print(f'Found {len(groups)} groups:')
    for g in groups:
        print(f' - ID={g.Id!r} Name={g.Name!r} normalized={normalize(g.Name)!r}')
    print('\nTarget:', target)
    print('target normalized:', normalize(target))
    matches = [g for g in groups if normalize(g.Name) == normalize(target)]
    if matches:
        print('\nNormalized match found:')
        for m in matches:
            print(f' -> ID={m.Id} Name={m.Name!r}')
    else:
        print('\nNo normalized match found. Also try exact match:')
        exact = [g for g in groups if g.Name == target]
        print('Exact matches:', len(exact))
    s.close()
