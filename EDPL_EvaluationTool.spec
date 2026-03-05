# -*- mode: python ; coding: utf-8 -*-
# =============================================================================
# PyInstaller spec file — EDPL Competence Evaluation Tool
# =============================================================================
# NE PAS lancer ce fichier directement. Utiliser les scripts de build :
#   Windows : BUILDING\build_windows.bat  (double-clic)
#   macOS   : BUILDING/build_mac.sh
#
# Ces scripts gèrent automatiquement :
#   - La numérotation de version (VERSION.txt + build_counter.txt dans BUILDING/)
#   - La sortie dans BUILDING\dist\EDPL_EvaluationTool\
#   - La journalisation dans BUILDING\build_log.txt
#
# En cas de compilation manuelle (depuis la racine projet) :
#   pyinstaller EDPL_EvaluationTool.spec --clean \
#       --distpath BUILDING/dist --workpath BUILDING/build_tmp
# =============================================================================

import sys
from pathlib import Path

block_cipher = None

# ---------------------------------------------------------------------------
# Fichiers de données à embarquer (templates, CSS, JS, uploads…)
# ---------------------------------------------------------------------------
added_datas = [
    ('templates',           'templates'),
    ('static',              'static'),
]

# ---------------------------------------------------------------------------
# Imports cachés nécessaires pour Flask / SQLAlchemy / extensions
# PyInstaller ne les détecte pas toujours automatiquement.
# ---------------------------------------------------------------------------
hidden = [
    # Flask & Werkzeug
    'flask',
    'flask.templating',
    'flask.globals',
    'flask_sqlalchemy',
    'werkzeug',
    'werkzeug.serving',
    'werkzeug.routing',
    'werkzeug.middleware.shared_data',
    'click',
    # SQLAlchemy
    'sqlalchemy',
    'sqlalchemy.orm',
    'sqlalchemy.ext.declarative',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.dialects.sqlite.pysqlite',
    # Jinja2
    'jinja2',
    'jinja2.ext',
    # Dépendances optionnelles
    'openpyxl',
    'openpyxl.styles',
    'openpyxl.utils',
    'bs4',
    'requests',
    'PIL',
    'PIL.Image',
    # Stdlib souvent manquants
    'email.mime.text',
    'email.mime.multipart',
    'logging.handlers',
]

a = Analysis(
    ['App_Main.py'],
    pathex=['.'],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclure les outils de dev non nécessaires en prod
        'pytest',
        'IPython',
        'notebook',
        'jupyter',
        'matplotlib',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='EDPL_EvaluationTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    # console=True  → fenêtre terminal visible (recommandé pour voir les erreurs)
    # Mettre False pour masquer le terminal (l'app se lance silencieusement)
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Icône optionnelle — décommenter si vous avez un .ico (Windows) ou .icns (macOS)
    # icon='static/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EDPL_EvaluationTool',
)
