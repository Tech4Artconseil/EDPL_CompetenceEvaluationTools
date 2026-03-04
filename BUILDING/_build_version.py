"""
_build_version.py — Calcul et incrémentation de version pour les scripts de build.

Usage (appelé par build_windows.bat ou build_mac.sh) :
    python BUILDING\_build_version.py <BUILDING_DIR>

Sortie sur stdout (parsée par le script appelant) :
    VER=v1.0-b003
    FULL=v1.0-b003_20260304
"""
import sys
import pathlib
import datetime

if len(sys.argv) < 2:
    print("Usage: python _build_version.py <BUILDING_DIR>", file=sys.stderr)
    sys.exit(1)

building_dir = pathlib.Path(sys.argv[1])

# Lire la version majeure
version_file = building_dir / "VERSION.txt"
base = version_file.read_text(encoding="utf-8").strip()

# Incrémenter le compteur
counter_file = building_dir / "build_counter.txt"
cnt = int(counter_file.read_text(encoding="utf-8").strip()) + 1
counter_file.write_text(str(cnt), encoding="utf-8")

# Construire les chaînes de version
ver = f"v{base}-b{cnt:03d}"
date = datetime.date.today().strftime("%Y%m%d")
full = f"{ver}_{date}"

print(f"VER={ver}")
print(f"FULL={full}")
