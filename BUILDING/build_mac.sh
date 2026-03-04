#!/bin/bash
# =============================================================================
# build_mac.sh — Compilation PyInstaller pour macOS
# =============================================================================
# Ce script est dans le sous-dossier BUILDING/
# Il remonte automatiquement à la racine du projet pour compiler.
#
# Versionnage :
#   BUILDING/VERSION.txt       → version majeure ex: 1.0  (éditable)
#   BUILDING/build_counter.txt → compteur auto-incrémenté
#   Version complète générée   → ex: v1.0-b003
#
# Sorties :
#   BUILDING/dist/EDPL_EvaluationTool/   ← dossier à distribuer (zipper)
#   BUILDING/build_log.txt               ← historique des builds
#
# Usage :
#   chmod +x build_mac.sh
#   ./build_mac.sh
# =============================================================================

set -e

echo ""
echo "========================================================"
echo "  EDPL Competence Evaluation Tool — Build macOS"
echo "========================================================"
echo ""

# --- Aller à la racine du projet (parent du dossier BUILDING) ---
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
BUILDING_DIR="$SCRIPT_DIR"

cd "$PROJECT_ROOT"
echo "Racine projet : $PROJECT_ROOT"
echo "Dossier build : $BUILDING_DIR"
echo ""

# --- Activation du venv si présent ---
echo "[1/6] Activation de l'environnement Python..."
if [ -f ".venv311/bin/activate" ]; then
    source .venv311/bin/activate
    echo "    venv: .venv311"
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "    venv: .venv"
else
    echo "    Aucun venv trouvé, utilisation du Python global."
fi

# --- Calcul de la version (via Python) ---
echo "[2/6] Calcul de la version..."
VERSION_INFO=$(python3 - <<'PYEOF'
import pathlib, datetime, sys
d = pathlib.Path("BUILDING")
base = (d / "VERSION.txt").read_text().strip()
cnt_f = d / "build_counter.txt"
cnt = int(cnt_f.read_text().strip()) + 1
cnt_f.write_text(str(cnt))
ver = f"v{base}-b{cnt:03d}"
date = datetime.date.today().strftime("%Y%m%d")
full = f"{ver}_{date}"
print(f"{ver}|{full}")
PYEOF
)

VER=$(echo "$VERSION_INFO" | cut -d'|' -f1)
FULL=$(echo "$VERSION_INFO" | cut -d'|' -f2)

echo "    Version : $VER"
echo "    Build   : $FULL"

# --- Installation / mise à jour de PyInstaller ---
echo "[3/6] Installation de PyInstaller..."
pip install --upgrade pyinstaller --quiet

# --- Nettoyage des anciens builds ---
echo "[4/6] Nettoyage de BUILDING/dist/ et BUILDING/build_tmp/..."
rm -rf "$BUILDING_DIR/dist"
rm -rf "$BUILDING_DIR/build_tmp"

# --- Compilation ---
echo "[5/6] Compilation avec PyInstaller..."
echo ""
pyinstaller EDPL_EvaluationTool.spec --clean \
    --distpath "$BUILDING_DIR/dist" \
    --workpath "$BUILDING_DIR/build_tmp"

# --- Déposer VERSION.txt dans le dossier distribué ---
echo "[6/6] Finalisation..."
DIST_DIR="$BUILDING_DIR/dist/EDPL_EvaluationTool"

cat > "$DIST_DIR/VERSION.txt" << VEOF
EDPL Competence Evaluation Tool
Version  : $VER
Build    : $FULL
Plateforme: macOS

Pour démarrer : clic droit sur EDPL_EvaluationTool → Ouvrir
Pour l'aide   : consulter GUIDE_DISTRIBUTION.md
VEOF

# Copier le guide de distribution dans le dist si disponible
if [ -f "$BUILDING_DIR/GUIDE_DISTRIBUTION.md" ]; then
    cp "$BUILDING_DIR/GUIDE_DISTRIBUTION.md" "$DIST_DIR/GUIDE_DISTRIBUTION.md"
fi

# --- Journalisation dans build_log.txt ---
BDATE=$(date '+%Y-%m-%d %H:%M')
echo "[$BDATE] $FULL - macOS - OK - $DIST_DIR" >> "$BUILDING_DIR/build_log.txt"

echo ""
echo "========================================================"
echo "  Build terminé avec succès !"
echo "  Version    : $VER"
echo "  Dossier    : BUILDING/dist/EDPL_EvaluationTool/"
echo "  À zipper   : EDPL_EvaluationTool_${VER}_macOS.zip"
echo "========================================================"
echo ""
echo "Contenu du dossier de distribution :"
ls "$DIST_DIR/"
echo ""
