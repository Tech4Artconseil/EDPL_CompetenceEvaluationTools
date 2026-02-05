"""
Temp script: backup DB then fill `Photo_Url` for students using naming convention
Usage:
    python scripts/fill_photo_urls_backup.py [--force]

- Creates a backup: instance/evaluat.db.bak.<timestamp>
- Fills `Studnt.Photo_Url` with the first candidate using trombi naming rule (no remote verification)
- Use --force to overwrite existing Photo_Url values
"""
import os
import sys
import shutil
from datetime import datetime
import argparse

# ensure parent package directory is on sys.path so App_Main can be imported
repo_root = os.path.dirname(os.path.dirname(__file__))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from App_Main import App
from Data_Models import Db, Studnt
from image_fetcher import name_parts, candidates, BASE_URL


def backup_db(db_path: str) -> str:
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    bak = f"{db_path}.bak.{ts}"
    shutil.copy2(db_path, bak)
    return bak


def choose_candidate_url(first: str, last: str):
    cands = candidates(first, last)
    if not cands:
        return None
    return f"{BASE_URL}{cands[0]}.jpg"


def main(force: bool):
    repo_root = os.path.dirname(os.path.dirname(__file__))
    db_path = os.path.join(repo_root, 'instance', 'evaluat.db')
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return

    print("Creating DB backup...")
    bak = backup_db(db_path)
    print(f"Backup created: {bak}")

    updated = 0
    skipped = 0
    errors = 0

    with App.app_context():
        studs = Studnt.query.order_by(Studnt.Id).all()
        for st in studs:
            try:
                if st.Photo_Url and not force:
                    skipped += 1
                    continue
                first, last = name_parts(st.Name)
                url = choose_candidate_url(first, last)
                if not url:
                    skipped += 1
                    continue
                st.Photo_Url = url
                Db.session.add(st)
                Db.session.commit()
                updated += 1
                print(f"Updated Id={st.Id} Name='{st.Name}' -> {url}")
            except Exception as e:
                Db.session.rollback()
                errors += 1
                print(f"Error updating Id={st.Id} Name='{st.Name}': {e}")

    print('\nSummary:')
    print(f"  Updated: {updated}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors:  {errors}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--force', action='store_true', help='Overwrite existing Photo_Url')
    args = parser.parse_args()
    main(force=args.force)
