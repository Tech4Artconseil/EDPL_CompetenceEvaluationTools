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
# Ordre de priorité : .venv311 (Python 3.11) avant .venv (Python 3.14+)
# SQLAlchemy 2.0.x est INCOMPATIBLE avec Python 3.14 — .venv311 obligatoire.
echo "[1/6] Activation de l'environnement Python..."
VENV_ACTIVATE=""

# Priorité 1 : .venv311 dans le dossier PARENT
if [ -f "$(dirname "$PROJECT_ROOT")/.venv311/bin/activate" ]; then
    VENV_ACTIVATE="$(dirname "$PROJECT_ROOT")/.venv311/bin/activate"
    echo "    Trouvé : .venv311 (dossier parent)"
# Priorité 2 : .venv311 dans la racine projet
elif [ -f "$PROJECT_ROOT/.venv311/bin/activate" ]; then
    VENV_ACTIVATE="$PROJECT_ROOT/.venv311/bin/activate"
    echo "    Trouvé : .venv311 (racine projet)"
# Priorité 3 : .venv dans le dossier PARENT  [ATTENTION : peut être Python 3.14]
elif [ -f "$(dirname "$PROJECT_ROOT")/.venv/bin/activate" ]; then
    VENV_ACTIVATE="$(dirname "$PROJECT_ROOT")/.venv/bin/activate"
    echo "    AVERTISSEMENT : utilisation de .venv (vérifiez que Python est < 3.14)"
# Priorité 4 : .venv dans la racine projet
elif [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    VENV_ACTIVATE="$PROJECT_ROOT/.venv/bin/activate"
    echo "    AVERTISSEMENT : utilisation de .venv (vérifiez que Python est < 3.14)"
else
    echo "    Aucun venv trouvé — utilisation du Python courant."
    echo "    ATTENTION : SQLAlchemy nécessite Python 3.11 ou 3.12 maximum."
fi

if [ -n "$VENV_ACTIVATE" ]; then
    source "$VENV_ACTIVATE" || { echo "[ERREUR] Echec de l'activation du venv : $VENV_ACTIVATE"; exit 1; }
fi

echo "    Python actif :"
python3 --version || { echo "[ERREUR] Python introuvable après activation."; exit 1; }

# --- Calcul de la version (via _build_version.py, identique à Windows) ---
echo "[2/6] Calcul de la version..."
python3 "$BUILDING_DIR/_build_version.py" "$BUILDING_DIR" > "$BUILDING_DIR/_ver_tmp.txt" || { echo "[ERREUR] Echec du calcul de version."; exit 1; }
while IFS='=' read -r key value; do
    case "$key" in
        VER)  VER="$value" ;;
        FULL) FULL="$value" ;;
    esac
done < "$BUILDING_DIR/_ver_tmp.txt"
rm -f "$BUILDING_DIR/_ver_tmp.txt"

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

# --- Génération et copie de la BDD seed (données de démo) ---
echo "Génération de la BDD seed..."
SEED_DB_TARGET="$DIST_DIR/instance/evaluat.db"
mkdir -p "$DIST_DIR/instance"
python3 "$BUILDING_DIR/create_seed_db.py" "$SEED_DB_TARGET"
if [ $? -ne 0 ]; then
    echo "    [AVERTISSEMENT] La génération de la BDD seed a échoué. La distribution démarrera sans données."
else
    echo "    BDD seed copiée : instance/evaluat.db"
fi

# --- Nettoyage du dossier trombi : conserver uniquement les images de démo ---
echo "Nettoyage du dossier trombi (images de demo uniquement)..."
TROMBI_DIR="$DIST_DIR/_internal/static/uploads/trombi"
DEMO_IMAGES="DUPONT_Alice.png MARTIN_Thomas.png BERNARD_Lea.png MOREAU_Julien.jpg PETIT_Emma.jpg"
if [ -d "$TROMBI_DIR" ]; then
    TROMBI_REMOVED=0
    for f in "$TROMBI_DIR"/*; do
        fname=$(basename "$f")
        keep=0
        for demo in $DEMO_IMAGES; do
            if [ "$fname" = "$demo" ]; then
                keep=1
                break
            fi
        done
        if [ $keep -eq 0 ]; then
            rm -f "$f"
            TROMBI_REMOVED=$((TROMBI_REMOVED + 1))
            echo "    Supprimé : $fname"
        fi
    done
    echo "    Trombi nettoyé : $TROMBI_REMOVED image(s) supprimée(s)."
else
    echo "    AVERTISSEMENT : dossier trombi introuvable dans la distribution."
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
