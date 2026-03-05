@echo off
setlocal enabledelayedexpansion
:: =============================================================================
:: build_windows.bat — Compilation PyInstaller pour Windows
:: =============================================================================
:: Ce script est dans le sous-dossier BUILDING/
:: Il remonte automatiquement a la racine du projet pour compiler.
::
:: Versionnage :
::   BUILDING\VERSION.txt       -> version majeure ex: 1.0  (editable)
::   BUILDING\build_counter.txt -> compteur auto-incremente
::   Version complete generee   -> ex: v1.0-b003
::
:: Sorties :
::   BUILDING\dist\EDPL_EvaluationTool\   <- dossier a distribuer (zipper)
::   BUILDING\build_log.txt               <- historique des builds
:: =============================================================================

echo.
echo ========================================================
echo   EDPL Competence Evaluation Tool - Build Windows
echo ========================================================
echo.

:: --- Aller a la racine du projet (parent du dossier BUILDING) ---
cd /d "%~dp0.."
set "PROJECT_ROOT=%CD%"
set "BUILDING_DIR=%PROJECT_ROOT%\BUILDING"

echo Racine projet : %PROJECT_ROOT%
echo Dossier build : %BUILDING_DIR%
echo.

:: ---------------------------------------------------------------------------
:: [1/6] Detection et activation du venv
:: Ordre de priorite : .venv311 (Python 3.11) avant .venv (Python 3.14+)
:: SQLAlchemy 2.0.x est INCOMPATIBLE avec Python 3.14 — .venv311 obligatoire.
:: Utilisation de GOTO pour eviter les cascades IF/ELSE IF en batch.
:: ---------------------------------------------------------------------------
echo [1/6] Activation de l'environnement Python...
set "VENV_ACTIVATE="
set "VENV_PYINSTALLER="

:: Priorite 1 : .venv311 dans le dossier PARENT (emplacement habituel)
IF EXIST "%PROJECT_ROOT%\..\.venv311\Scripts\activate.bat" (
    set "VENV_ACTIVATE=%PROJECT_ROOT%\..\.venv311\Scripts\activate.bat"
    set "VENV_PYINSTALLER=%PROJECT_ROOT%\..\.venv311\Scripts\pyinstaller.exe"
    echo     Trouve : .venv311 ^(dossier parent^)
    goto :do_activate
)
:: Priorite 2 : .venv311 dans la racine projet
IF EXIST "%PROJECT_ROOT%\.venv311\Scripts\activate.bat" (
    set "VENV_ACTIVATE=%PROJECT_ROOT%\.venv311\Scripts\activate.bat"
    set "VENV_PYINSTALLER=%PROJECT_ROOT%\.venv311\Scripts\pyinstaller.exe"
    echo     Trouve : .venv311 ^(racine projet^)
    goto :do_activate
)
:: Priorite 3 : .venv dans le dossier PARENT  [ATTENTION : peut etre Python 3.14]
IF EXIST "%PROJECT_ROOT%\..\.venv\Scripts\activate.bat" (
    set "VENV_ACTIVATE=%PROJECT_ROOT%\..\.venv\Scripts\activate.bat"
    set "VENV_PYINSTALLER=%PROJECT_ROOT%\..\.venv\Scripts\pyinstaller.exe"
    echo     AVERTISSEMENT : utilisation de .venv ^(verifiez que Python est < 3.14^)
    goto :do_activate
)
:: Priorite 4 : .venv dans la racine projet
IF EXIST "%PROJECT_ROOT%\.venv\Scripts\activate.bat" (
    set "VENV_ACTIVATE=%PROJECT_ROOT%\.venv\Scripts\activate.bat"
    set "VENV_PYINSTALLER=%PROJECT_ROOT%\.venv\Scripts\pyinstaller.exe"
    echo     AVERTISSEMENT : utilisation de .venv ^(verifiez que Python est < 3.14^)
    goto :do_activate
)
echo     Aucun venv trouve - utilisation du Python courant.
echo     ATTENTION : SQLAlchemy necessite Python 3.11 ou 3.12 maximum.
goto :after_activate

:do_activate
call "%VENV_ACTIVATE%"
IF %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Echec de l'activation du venv : %VENV_ACTIVATE%
    pause
    exit /b 1
)

:after_activate
:: Afficher la version Python utilisee pour verification
echo     Python actif :
python --version
IF %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Python introuvable apres activation.
    pause
    exit /b 1
)

:: ---------------------------------------------------------------------------
:: [2/6] Calcul de la version
:: ---------------------------------------------------------------------------
echo [2/6] Calcul de la version...
python "%BUILDING_DIR%\_build_version.py" "%BUILDING_DIR%" > "%BUILDING_DIR%\_ver_tmp.txt"
IF %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Echec du calcul de version.
    pause
    exit /b 1
)
for /f "tokens=1,2 delims==" %%a in (%BUILDING_DIR%\_ver_tmp.txt) do set "%%a=%%b"
del "%BUILDING_DIR%\_ver_tmp.txt" >nul 2>&1
echo     Version : %VER%
echo     Build   : %FULL%

:: ---------------------------------------------------------------------------
:: [3/6] Installation / mise a jour de PyInstaller
:: ---------------------------------------------------------------------------
echo [3/6] Installation de PyInstaller...
pip install --upgrade pyinstaller --quiet
IF %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Impossible d'installer PyInstaller.
    pause
    exit /b 1
)
:: Determiner l'executable PyInstaller a utiliser
IF NOT "%VENV_PYINSTALLER%"=="" (
    IF EXIST "%VENV_PYINSTALLER%" (
        set "PYINSTALLER_EXE=%VENV_PYINSTALLER%"
    ) ELSE (
        set "PYINSTALLER_EXE=pyinstaller"
    )
) ELSE (
    set "PYINSTALLER_EXE=pyinstaller"
)
echo     PyInstaller : %PYINSTALLER_EXE%

:: ---------------------------------------------------------------------------
:: [4/6] Nettoyage
:: ---------------------------------------------------------------------------
echo [4/6] Nettoyage de BUILDING\dist\ et BUILDING\build_tmp\...
IF EXIST "%BUILDING_DIR%\dist"      rmdir /s /q "%BUILDING_DIR%\dist"
IF EXIST "%BUILDING_DIR%\build_tmp" rmdir /s /q "%BUILDING_DIR%\build_tmp"

:: ---------------------------------------------------------------------------
:: [5/6] Compilation
:: ---------------------------------------------------------------------------
echo [5/6] Compilation avec PyInstaller...
echo.
"%PYINSTALLER_EXE%" EDPL_EvaluationTool.spec --clean ^
    --distpath "%BUILDING_DIR%\dist" ^
    --workpath "%BUILDING_DIR%\build_tmp"

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERREUR] La compilation a echoue. Verifiez les messages ci-dessus.
    pause
    exit /b 1
)

:: ---------------------------------------------------------------------------
:: [6/6] Finalisation
:: ---------------------------------------------------------------------------
echo [6/6] Finalisation...
set "DIST_DIR=%BUILDING_DIR%\dist\EDPL_EvaluationTool"

(
    echo EDPL Competence Evaluation Tool
    echo Version   : %VER%
    echo Build     : %FULL%
    echo Plateforme: Windows
    echo.
    echo Pour demarrer : double-cliquer sur EDPL_EvaluationTool.exe
    echo Pour l'aide   : consulter GUIDE_DISTRIBUTION.md
) > "%DIST_DIR%\VERSION.txt"

IF EXIST "%BUILDING_DIR%\GUIDE_DISTRIBUTION.md" (
    copy /y "%BUILDING_DIR%\GUIDE_DISTRIBUTION.md" "%DIST_DIR%\GUIDE_DISTRIBUTION.md" >nul
)

:: --- Génération et copie de la BDD seed (données de démo) ---
echo Génération de la BDD seed...
set "SEED_DB_TARGET=%DIST_DIR%\instance\evaluat.db"
if not exist "%DIST_DIR%\instance" mkdir "%DIST_DIR%\instance"
python "%BUILDING_DIR%\create_seed_db.py" "%SEED_DB_TARGET%"
IF %ERRORLEVEL% NEQ 0 (
    echo [AVERTISSEMENT] La génération de la BDD seed a échoué. La distribution démarrera sans données.
) ELSE (
    echo     BDD seed copiée : instance\evaluat.db
)

:: --- Nettoyage du dossier trombi : conserver uniquement les images de démo ---
echo Nettoyage du dossier trombi (images de demo uniquement)...
set "TROMBI_DIR=%DIST_DIR%\_internal\static\uploads\trombi"
IF EXIST "%TROMBI_DIR%" (
    set "TROMBI_REMOVED=0"
    for %%f in ("%TROMBI_DIR%\*") do (
        set "KEEP="
        if /i "%%~nxf"=="DUPONT_Alice.png"   set "KEEP=1"
        if /i "%%~nxf"=="MARTIN_Thomas.png"  set "KEEP=1"
        if /i "%%~nxf"=="BERNARD_Lea.png"    set "KEEP=1"
        if /i "%%~nxf"=="MOREAU_Julien.jpg"  set "KEEP=1"
        if /i "%%~nxf"=="PETIT_Emma.jpg"     set "KEEP=1"
        if not defined KEEP (
            del /f /q "%%f"
            set /a TROMBI_REMOVED+=1
            echo     Supprime : %%~nxf
        )
    )
    echo     Trombi nettoye : !TROMBI_REMOVED! image^(s^) supprimee^(s^).
) ELSE (
    echo     AVERTISSEMENT : dossier trombi introuvable dans la distribution.
)

for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set "BDATE=%%a/%%b/%%c"
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "BTIME=%%a:%%b"
>> "%BUILDING_DIR%\build_log.txt" echo [%BDATE% %BTIME%] %FULL% - Windows - OK - %DIST_DIR%

echo.
echo ========================================================
echo   Build termine avec succes !
echo   Version    : %VER%
echo   Dossier    : BUILDING\dist\EDPL_EvaluationTool\
echo   A zipper   : EDPL_EvaluationTool_%VER%_Windows.zip
echo ========================================================
echo.
echo Contenu du dossier de distribution :
dir /b "%DIST_DIR%"
echo.
pause
