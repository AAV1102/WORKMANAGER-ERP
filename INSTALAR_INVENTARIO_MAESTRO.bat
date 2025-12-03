@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ======================================================================
REM Gestor de Base de Datos - WorkManager ERP
REM Este script es llamado por start.bat
REM ======================================================================

set "PROJECT_ROOT=%~dp0"
set "VENV_PYTHON=%PROJECT_ROOT%.venv\Scripts\python.exe"

:SUBMENU_DB
cls
color 0B
echo ================================================================
echo                 GESTION DE BASE DE DATOS
echo ================================================================
echo 1. Crear/Inicializar Base de Datos
echo 2. Importar datos (importador masivo)
echo 3. Iniciar servidor Flask
echo 4. Verificar instalacion
echo 5. Buscar equipo por serial
echo 6. Salir
echo.
set /p "opcion=Selecciona una opcion: "

if "%opcion%"=="1" goto CREAR_DB
if "%opcion%"=="2" goto IMPORTAR
if "%opcion%"=="3" goto FLASK
if "%opcion%"=="4" goto VERIFICAR
if "%opcion%"=="5" goto BUSCAR
goto :EOF

:CREAR_DB
echo.
echo ================================================================
echo CREANDO TABLAS EN workmanager_erp.db (si no existen)
echo ================================================================
echo.
echo Este script ahora utiliza 'create_production_db.py' para asegurar que la
echo base de datos local sea identica a la de produccion.
echo.
cd /d "%PROJECT_ROOT%"
"%VENV_PYTHON%" create_production_db.py
pause
goto SUBMENU_DB

:IMPORTAR
echo.
echo ================================================================
echo IMPORTANDO DATOS A workmanager_erp.db
echo ================================================================
echo.
cd /d "%PROJECT_ROOT%scripts\inventario"
if exist "importador_masivo_workmanager.py" (
    "%VENV_PYTHON%" importador_masivo_workmanager.py
    echo [OK] Importacion completada.
) else (
    echo [ERROR] No se encontro importador_masivo_workmanager.py en %SCRIPTS_DIR%
)
pause
goto SUBMENU_DB

:FLASK
echo.
echo Iniciando WorkManager ERP en http://localhost:5000
cd /d "%PROJECT_ROOT%"
"%VENV_PYTHON%" "%PROJECT_ROOT%run.py"
goto SUBMENU_DB

:VERIFICAR
echo.
cd /d "%PROJECT_ROOT%"
if exist "%PROJECT_ROOT%workmanager_erp.db" (
    echo [OK] workmanager_erp.db encontrada.
    "%VENV_PYTHON%" -c "import sqlite3; conn = sqlite3.connect('workmanager_erp.db'); c = conn.cursor(); print('--- Conteo de Registros ---'); [print(f'{table+':':<30} {c.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]:,}') if c.execute(f'SELECT name FROM sqlite_master WHERE type=\'table\' AND name=\'{table}\'').fetchone() else print(f'{table+':':<30} NO EXISTE') for table in ['equipos_individuales', 'equipos_agrupados', 'sedes', 'empleados', 'licencias_office365', 'inventario_administrativo']]; conn.close()"
 else (
    echo [ERROR] workmanager_erp.db NO encontrada.
)
pause
goto SUBMENU_DB

:BUSCAR
echo.
set "serial_a_buscar="
set /p "serial_a_buscar=Introduce el serial a buscar (o presiona Enter para cancelar): "
if not defined serial_a_buscar (
    echo [INFO] Búsqueda cancelada.
    goto SUBMENU_DB
)

cd /d "%PROJECT_ROOT%"
set "SEARCH_SERIAL=%serial_a_buscar%"
"%VENV_PYTHON%" -c "import sqlite3, os, json; serial = os.environ.get('SEARCH_SERIAL', ''); conn = sqlite3.connect('workmanager_erp.db'); conn.row_factory = sqlite3.Row; c = conn.cursor(); c.execute('SELECT * FROM equipos_individuales WHERE serial LIKE ?', ('%' + serial + '%',)); row = c.fetchone(); print(f'--- Resultado para \"{serial}\" ---'); print('Encontrado:' if row else 'No encontrado.'); print(json.dumps(dict(row), indent=2, ensure_ascii=False)) if row else ''"
pause
goto SUBMENU_DB

endlocal
