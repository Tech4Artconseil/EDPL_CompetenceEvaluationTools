#!/usr/bin/env python
"""Run a dry-run of the student-sheet filler and print a JSON report.

Usage:
    .venv\Scripts\python scripts\run_fill_dryrun.py --evaluat 7

If you get import/SQLAlchemy errors, run this script with the same Python interpreter you use to run the app.
"""
import json
import argparse
import traceback
import sys
from pathlib import Path

# Ensure project package root is on sys.path so imports like `from App_Main import App` work
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def _print_compact_log(res: dict):
    actions = res.get('actions', []) or []
    if not actions:
        print('Aucune action à afficher')
        return
    from collections import defaultdict
    grouped = defaultdict(list)
    for a in actions:
        grouped[a.get('sheet', '?')].append(a)

    def sheet_key(s):
        try:
            return int(s)
        except Exception:
            return s

    for sheet in sorted(grouped.keys(), key=sheet_key):
        print(f"Feuille {sheet}:")
        for a in grouped[sheet]:
            st = a.get('status')
            if st in ('start_processing', 'end_processing'):
                continue
            if st == 'mapped_by_index':
                print(f"  -> index -> {a.get('student')}")
            elif st == 'student_not_found':
                print(f"  ! student_not_found: {a.get('name')}")
            elif st == 'no_student_name':
                print("  ! no_student_name")
            elif st == 'skill_not_found':
                print(f"  - row {a.get('row')}: skill_not_found {a.get('skill')}")
            elif 'to' in a:
                print(f"  + row {a.get('row')}: {a.get('skill')} -> 1 (was: {a.get('from')}) for {a.get('student')}")
            elif st == 'skipped_nonzero':
                print(f"  - row {a.get('row')}: {a.get('skill')} skipped (value: {a.get('value')})")
            elif st == 'level_out_of_range':
                print(f"  - row {a.get('row')}: {a.get('skill')} level_out_of_range {a.get('level')}")
            elif st == 'error':
                print(f"  ! error: {a.get('error')}")
            else:
                print(f"  * {a}")


def main(evaluat_id: int, print_log: bool = False):
    try:
        from App_Main import App
        from sheets_local import fill_student_sheets
    except Exception:
        traceback.print_exc()
        print('\nFailed to import app or sheets module. Make sure to run this inside the project venv.')
        return 2

    try:
        with App.app_context():
            # default: dry-run
            res = fill_student_sheets(evaluat_id=evaluat_id, dry_run=True)
            # ensure non-serializable objects (openpyxl types like ArrayFormula) are converted to strings
            if print_log:
                _print_compact_log(res)
            else:
                print(json.dumps(res, ensure_ascii=False, indent=2, default=str))

            # if commit requested, perform real write and show result paths
            return res
    except Exception:
        traceback.print_exc()
        return 3


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--evaluat', '-e', type=int, default=7, help='Evaluat id to run the dry-run for')
    p.add_argument('--log', '-l', action='store_true', help='Print a compact human-readable log instead of JSON')
    p.add_argument('--commit', '-c', action='store_true', help='Also perform the real write (save XLSX + JSON report)')
    p.add_argument('--force', '-f', action='store_true', help='When committing, overwrite formula/unevaluated cells')
    args = p.parse_args()
    res = main(args.evaluat, print_log=args.log)
    # when commit requested, run the real write and print outcome
    if args.commit:
        try:
            from App_Main import App
            from sheets_local import fill_student_sheets
            with App.app_context():
                real = fill_student_sheets(evaluat_id=args.evaluat, dry_run=False, overwrite_formulas=args.force)
                # print compact log then path
                if args.log:
                    _print_compact_log(real)
                else:
                    print(json.dumps(real, ensure_ascii=False, indent=2, default=str))
                if real.get('report_path'):
                    print('\nReport written to:', real['report_path'])
                if real.get('path'):
                    print('Filled workbook written to:', real['path'])
        except Exception:
            traceback.print_exc()
            print('Commit run failed')
    raise SystemExit(0)
