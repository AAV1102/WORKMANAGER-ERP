@echo off
chcp 65001 >nul
color 0A
setlocal enabledelayedexpansion

REM ======================================================================
REM Instalador / lanzador Inventario Maestro - WorkManager ERP
REM Este .bat asume que se ejecuta desde la carpeta raíz del proyecto
REM ======================================================================

set "PROJECT_ROOT=%~dp0"
set "VENV_PYTHON=%PROJECT_ROOT%.venv\Scripts\python.exe"
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
echo 1. Crear/Inicializar Base de Datos
echo 2. Importar datos (importador masivo)
echo 3. Iniciar servidor Flask
echo 4. Verificar instalacion
echo 5. Buscar equipo por serial
echo 6. Salir
echo.
set /p "opcion=Selecciona una opcion [1-6]: "

if "%opcion%"=="1" goto CREAR_DB
if "%opcion%"=="2" goto IMPORTAR
if "%opcion%"=="3" goto FLASK
if "%opcion%"=="4" goto VERIFICAR
if "%opcion%"=="5" goto BUSCAR
goto FIN

:CREAR_DB
echo.
echo ================================================================
echo CREANDO TABLAS EN workmanager_erp.db (si no existen)
echo ================================================================
echo.
cd /d "%PROJECT_ROOT%"
"%VENV_PYTHON%" - <<PY
import sqlite3

DB_PATH = "workmanager_erp.db"

tables = {
    "equipos_individuales": """
        CREATE TABLE IF NOT EXISTS equipos_individuales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_barras_individual TEXT UNIQUE,            
            entrada_oc_compra TEXT,
            cargado_nit TEXT,
            enviado_nit TEXT,
            ciudad TEXT,
            tecnologia TEXT,
            serial TEXT,
            modelo TEXT,
            anterior_asignado TEXT,
            anterior_placa TEXT,
            placa TEXT,
            marca TEXT,
            procesador TEXT,
            arch_ram TEXT,
            cantidad_ram TEXT,
            tipo_disco TEXT,
            espacio_disco TEXT,
            so TEXT,
            estado TEXT,
            asignado_nuevo TEXT,
            fecha TEXT,
            fecha_llegada TEXT,
            area TEXT,
            marca_monitor TEXT,
            modelo_monitor TEXT,
            serial_monitor TEXT,
            placa_monitor TEXT,
            proveedor TEXT,
            oc TEXT,
            observaciones TEXT,
            disponible TEXT,
            sede_id INTEGER,
            ip_sede TEXT,
            creador_registro TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP,
            mac TEXT,
            hostname TEXT,
            ip TEXT,
            cargo TEXT,
            contacto TEXT,
            fecha_enviado TEXT,
            guia TEXT
        );
    """,
    "equipos_agrupados": """
        CREATE TABLE IF NOT EXISTS equipos_agrupados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_barras_unificado TEXT UNIQUE,
            descripcion_general TEXT,
            estado_general TEXT,
            asignado_actual TEXT,
            sede_id INTEGER,
            observaciones TEXT,
            creador_registro TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "sedes": "CREATE TABLE IF NOT EXISTS sedes (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, ciudad TEXT);",
    "empleados": "CREATE TABLE IF NOT EXISTS empleados (id INTEGER PRIMARY KEY, nombre TEXT, cargo TEXT, area TEXT);",
    "licencias_office365": "CREATE TABLE IF NOT EXISTS licencias_office365 (id INTEGER PRIMARY KEY, email TEXT UNIQUE, tipo_licencia TEXT, asignado_a TEXT);",
    "inventario_administrativo": "CREATE TABLE IF NOT EXISTS inventario_administrativo (id INTEGER PRIMARY KEY, item TEXT, cantidad INTEGER, ubicacion TEXT);"
}

try:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    print(f"[OK] Conectado a la base de datos: {DB_PATH}")
    for table_name, create_sql in tables.items():
        try:
            c.execute(create_sql)
            print(f"  - Tabla '{table_name}' asegurada.")
        except sqlite3.Error as e:
            print(f"  - [ERROR] al crear tabla '{table_name}': {e}")
    
    # Crear un trigger para actualizar 'fecha_actualizacion' en 'equipos_individuales'
    try:
        c.execute("""
            CREATE TRIGGER IF NOT EXISTS update_equipos_individuales_fecha_actualizacion
            AFTER UPDATE ON equipos_individuales FOR EACH ROW
            BEGIN
                UPDATE equipos_individuales SET fecha_actualizacion = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
        """)
        print("  - Trigger 'update_equipos_individuales_fecha_actualizacion' asegurado.")
    except sqlite3.Error as e:
        print(f"  - [ERROR] al crear el trigger: {e}")

    conn.commit()
    print("[OK] Proceso de creacion de tablas finalizado.")
except sqlite3.Error as e:
    print(f"[ERROR] No se pudo conectar o escribir en la base de datos: {e}")
finally:
    if conn:
        conn.close()
PY
pause
goto FIN

:IMPORTAR
echo.
echo ================================================================
echo IMPORTANDO DATOS A workmanager_erp.db
echo ================================================================
echo.
cd /d "%SCRIPTS_DIR%"
if exist "importador_masivo_workmanager.py" (
    "%VENV_PYTHON%" importador_masivo_workmanager.py
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
"%VENV_PYTHON%" app.py
goto FIN

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
goto FIN

:BUSCAR
echo.
set "serial_a_buscar="
set /p "serial_a_buscar=Introduce el serial a buscar (o presiona Enter para cancelar): "
if not defined serial_a_buscar (
    echo [INFO] Búsqueda cancelada.
    goto FIN
)

cd /d "%PROJECT_ROOT%"
set "SEARCH_SERIAL=%serial_a_buscar%"
"%VENV_PYTHON%" -c "import sqlite3, os, json; serial = os.environ.get('SEARCH_SERIAL', ''); conn = sqlite3.connect('workmanager_erp.db'); conn.row_factory = sqlite3.Row; c = conn.cursor(); c.execute('SELECT * FROM equipos_individuales WHERE serial LIKE ?', ('%' + serial + '%',)); row = c.fetchone(); print(f'--- Resultado para \"{serial}\" ---'); print('Encontrado:' if row else 'No encontrado.'); print(json.dumps(dict(row), indent=2, ensure_ascii=False)) if row else ''"
pause
goto FIN

:FIN
echo.
echo =====================================================================
echo Gracias por usar WorkManager ERP - Inventario Maestro
echo =====================================================================
endlocal
exit /b
