import sqlite3
import sys
import os

DB = os.path.join(os.path.dirname(__file__), 'EDPL_CompetenceEvaluationTools', 'instance', 'evaluat.db')

def usage():
    print('Usage: python check_evaluat_scores.py <evaluat_id>')

def main():
    if len(sys.argv) < 2:
        usage(); sys.exit(1)
    eid = sys.argv[1]
    if not os.path.exists(DB):
        print('DB not found at', DB); sys.exit(1)
    con = sqlite3.connect(DB)
    cur = con.cursor()

    # number of students in the evaluation's group
    cur.execute('SELECT Group_Id, SkillSet_Id FROM evaluats WHERE Id = ?', (eid,))
    row = cur.fetchone()
    if not row:
        print('No evaluation with Id', eid); sys.exit(1)
    group_id, skillset = row
    cur.execute('SELECT COUNT(*) FROM studnts WHERE Group_Id = ?', (group_id,))
    n_students = cur.fetchone()[0]

    # number of skills for this skillset
    cur.execute('SELECT COUNT(*) FROM skills WHERE SkillSet_Id = ?', (skillset,))
    n_skills = cur.fetchone()[0]

    # expected score entries
    expected = n_students * n_skills
    cur.execute('SELECT COUNT(*) FROM scores WHERE Evaluat_Id = ?', (eid,))
    actual = cur.fetchone()[0]

    print('Evaluat Id:', eid)
    print(' Group_Id:', group_id, ' Students:', n_students)
    print(' SkillSet_Id:', skillset, ' Skills:', n_skills)
    print(' Expected score entries:', expected)
    print(' Actual score entries:', actual)

    if actual < expected:
        print('MISSING entries: ', expected - actual)
    elif actual > expected:
        print('EXTRA entries: ', actual - expected)
    else:
        print('OK - score entries match expected count')

    con.close()

if __name__ == '__main__':
    main()
