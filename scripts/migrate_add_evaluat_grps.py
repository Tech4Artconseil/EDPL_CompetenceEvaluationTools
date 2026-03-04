"""
scripts/migrate_add_evaluat_grps.py
-----------------------------------
Crée les tables evaluat_grps et evaluat_grp_members si elles n'existent pas.
Peut être relancé sans danger (CREATE TABLE IF NOT EXISTS).

Usage:
    python scripts/migrate_add_evaluat_grps.py
"""

import os
import sys

# Ajoute le répertoire parent (package) au path pour importer App_Main et Data_Models
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
sys.path.insert(0, PACKAGE_DIR)

from App_Main import App
from Data_Models import Db, EvaluatGrp, EvaluatGrpMember  # noqa: F401

DDL_EVALUAT_GRPS = """
CREATE TABLE IF NOT EXISTS evaluat_grps (
    "Id"         INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "Name"       VARCHAR(100) NOT NULL,
    "Evaluat_Id" INTEGER NOT NULL REFERENCES evaluats ("Id"),
    "CreatedAt"  DATETIME
);
"""

DDL_EVALUAT_GRP_MEMBERS = """
CREATE TABLE IF NOT EXISTS evaluat_grp_members (
    "Id"             INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "EvaluatGrp_Id"  INTEGER NOT NULL REFERENCES evaluat_grps ("Id"),
    "Studnt_Id"      INTEGER NOT NULL REFERENCES studnts ("Id")
);
"""

DDL_INDEX_GRP = """
CREATE INDEX IF NOT EXISTS ix_evaluat_grp_members_grp
    ON evaluat_grp_members ("EvaluatGrp_Id");
"""

DDL_INDEX_STUDNT = """
CREATE INDEX IF NOT EXISTS ix_evaluat_grp_members_studnt
    ON evaluat_grp_members ("Studnt_Id");
"""

with App.app_context():
    conn = Db.engine.raw_connection()
    cursor = conn.cursor()
    for stmt in (DDL_EVALUAT_GRPS, DDL_EVALUAT_GRP_MEMBERS, DDL_INDEX_GRP, DDL_INDEX_STUDNT):
        cursor.execute(stmt)
    conn.commit()
    cursor.close()
    conn.close()
    print("Migration terminée : tables evaluat_grps et evaluat_grp_members créées (ou déjà existantes).")
