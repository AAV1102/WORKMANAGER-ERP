@echo off
chcp 65001 >nul
color 0A
setlocal

REM ======================================================================
REM Instalador / lanzador Inventario Maestro - WorkManager ERP
REM Este .bat asume que se ejecuta desde la carpeta raíz del proyecto
REM C:\Users\anderson.a\Documents\TODO COMBINADO\flask-todo-app
REM ======================================================================

set "PROJECT_ROOT=%~dp0"
set "APP_FILE=%PROJECT_ROOT%app.py"
set "SCRIPTS_DIR=%PROJECT_ROOT%scripts\inventario"
set "MODULES_DIR=%PROJECT_ROOT%modules"
set "DOCS_DIR=%PROJECT_ROOT%docs\inventario"
set "LOG_DIR=%PROJECT_ROOT%logs"
set "UPLOADS_DIR=%PROJECT_ROOT%uploads"

echo ================================================================
echo WORKMANAGER ERP - INSTALADOR / IMPORTADOR INVENTARIO MAESTRO
echo Raiz del proyecto: %PROJECT_ROOT%
echo ================================================================
echo.

echo [1/5] Verificando proyecto...
if not exist "%APP_FILE%" (
    echo [ERROR] No se encontro app.py en %PROJECT_ROOT%
    echo Asegurate de ejecutar este .bat desde la carpeta raiz del proyecto.
    pause
    exit /b 1
)
echo [OK] Proyecto Flask encontrado.

echo.
echo [2/5] Creando carpetas necesarias...
if not exist "%SCRIPTS_DIR%" mkdir "%SCRIPTS_DIR%"
if not exist "%MODULES_DIR%\inventario_maestro" mkdir "%MODULES_DIR%\inventario_maestro%"
if not exist "%DOCS_DIR%" mkdir "%DOCS_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
if not exist "%UPLOADS_DIR%" mkdir "%UPLOADS_DIR%"
echo [OK] Carpetas listas.

echo.
echo [3/5] Copiando archivos de soporte (si existen junto al .bat)...
if exist "%PROJECT_ROOT%importador_masivo_workmanager.py" copy /Y "%PROJECT_ROOT%importador_masivo_workmanager.py" "%SCRIPTS_DIR%\" >nul
if exist "%PROJECT_ROOT%extensiones_inventarios.py" copy /Y "%PROJECT_ROOT%extensiones_inventarios.py" "%MODULES_DIR%\" >nul
if exist "%PROJECT_ROOT%GUIA_INTEGRACION_FINAL.md" copy /Y "%PROJECT_ROOT%GUIA_INTEGRACION_FINAL.md" "%DOCS_DIR%\" >nul
if exist "%PROJECT_ROOT%README.md" copy /Y "%PROJECT_ROOT%README.md" "%DOCS_DIR%\README_INVENTARIO_MAESTRO.md" >nul
echo [OK] Copia finalizada (se ignoran faltantes silenciosamente).

echo.
echo [4/5] Configurando importador masivo...
(
echo # Configuracion del Importador Masivo
echo CARPETA_ORIGEN = r"%UPLOADS_DIR%"
echo DB_PATH = "workmanager_erp.db"
echo CHUNK_SIZE = 500
) > "%SCRIPTS_DIR%\config_importador.py"
echo [OK] Configuracion escrita en scripts\inventario\config_importador.py

echo.
echo [5/5] Menu de acciones
echo 1. Importar datos (importador masivo)
echo 2. Iniciar servidor Flask
echo 3. Verificar instalacion
echo 4. Buscar serial MP2B7YWL
echo 5. Salir
echo.
set /p "opcion=Selecciona una opcion [1-5]: "

if "%opcion%"=="1" goto IMPORTAR
if "%opcion%"=="2" goto FLASK
if "%opcion%"=="3" goto VERIFICAR
if "%opcion%"=="4" goto BUSCAR
goto FIN

:IMPORTAR
echo.
echo ================================================================
echo IMPORTANDO DATOS A workmanager_erp.db
echo ================================================================
echo.
cd /d "%SCRIPTS_DIR%"
if exist "importador_masivo_workmanager.py" (
    python importador_masivo_workmanager.py
    echo [OK] Importacion completada.
) else (
    echo [ERROR] No se encontro importador_masivo_workmanager.py en %SCRIPTS_DIR%
)
pause
goto FIN

:FLASK
echo.
echo Iniciando WorkManager ERP en http://localhost:5000
cd /d "%PROJECT_ROOT%"
python app.py
goto FIN

:VERIFICAR
echo.
cd /d "%PROJECT_ROOT%"
if exist "workmanager_erp.db" (
    echo [OK] workmanager_erp.db encontrada.
    python - <<PY
import sqlite3
conn = sqlite3.connect("workmanager_erp.db")
c = conn.cursor()
for table in ["equipos_individuales","sedes","licencias_office365","empleados","inventario_administrativo"]:
    try:
        c.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"{table}: {c.fetchone()[0]:,}")
    except Exception as e:
        print(f"{table}: error {e}")
conn.close()
PY
) else (
    echo [ERROR] workmanager_erp.db NO encontrada.
)
pause
goto FIN

:BUSCAR
echo.
cd /d "%PROJECT_ROOT%"
python - <<PY
import sqlite3
conn = sqlite3.connect("workmanager_erp.db")
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT * FROM equipos_individuales WHERE serial LIKE '%MP2B7YWL%'")
row = c.fetchone()
print("Encontrado:" if row else "No encontrado")
if row: print(dict(row))
conn.close()
PY
pause
goto FIN

:FIN
echo.
echo =====================================================================
echo Gracias por usar WorkManager ERP - Inventario Maestro
echo =====================================================================
endlocal
exit /b
