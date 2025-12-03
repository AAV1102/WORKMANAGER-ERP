@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"
set "VENV_PYTHON=%PROJECT_ROOT%.venv\Scripts\python.exe"

:MAIN_MENU
cls
color 0A
echo ======================================================================
echo                 WORKMANAGER ERP - CENTRO DE CONTROL
echo ======================================================================
echo.
echo  --- Desarrollo y Ejecucion ---
echo  1. Iniciar Servidor de Desarrollo Local
echo.
echo  --- Gestion de Datos ---
echo  2. Gestionar Base de Datos (Crear, Importar, Verificar)
echo  3. Realizar Copia de Seguridad (Backup)
echo  4. Migrar Datos a Produccion (Render, Vercel, etc.)
echo.
echo  --- Control de Versiones (GitHub) ---
echo  5. Subir Cambios a GitHub
echo  6. Iniciar Sincronizacion Automatica en segundo plano
echo.
echo  --- Herramientas Avanzadas (USAR CON CUIDADO) ---
echo  7. Limpiar Historial del Repositorio (para errores de tamano)
echo  8. Forzar Sincronizacion con GitHub (sobrescribe la nube)
echo.
echo  0. Salir
echo.
echo ======================================================================
echo.
set /p "CHOICE=Selecciona una opcion y presiona Enter: "

if "%CHOICE%"=="1" goto INICIAR_LOCAL
if "%CHOICE%"=="2" goto GESTIONAR_DB
if "%CHOICE%"=="3" goto BACKUP
if "%CHOICE%"=="4" goto MIGRATE_PROD_UNIFIED
if "%CHOICE%"=="5" goto GIT_PUSH
if "%CHOICE%"=="6" goto SYNC_AUTO
if "%CHOICE%"=="7" goto CLEAN_REPO
if "%CHOICE%"=="8" goto FORCE_PUSH
if "%CHOICE%"=="0" goto :EOF

echo Opcion no valida.
pause
goto MAIN_MENU

:INICIAR_LOCAL
cls
echo --- INICIANDO SERVIDOR DE DESARROLLO ---
call :PREPARAR_ENTORNO
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudo preparar el entorno. Abortando.
    pause
    goto MAIN_MENU
)

echo.
echo [OK] Entorno listo. Iniciando servidor Flask...
"%VENV_PYTHON%" "%PROJECT_ROOT%run.py"

echo.
echo Servidor detenido.
pause
goto MAIN_MENU

:GESTIONAR_DB
cls
echo --- GESTION DE BASE DE DATOS ---
call :PREPARAR_ENTORNO
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudo preparar el entorno. Abortando.
    pause
    goto MAIN_MENU
)

:SUBMENU_DB
cls
color 0B
echo ================================================================
echo                 GESTION DE BASE DE DATOS
echo ================================================================
echo 1. Crear/Inicializar Base de Datos Local
echo 2. Importar datos desde archivos (Importador Masivo)
echo 3. Verificar estado de la Base de Datos
echo 4. Buscar equipo por serial
echo.
echo 0. Volver al Menu Principal
echo.
set /p "opcion=Selecciona una opcion: "

if "%opcion%"=="1" goto CREAR_DB_LOCAL
if "%opcion%"=="2" goto IMPORTAR_MASIVO
if "%opcion%"=="3" goto VERIFICAR_DB
if "%opcion%"=="4" goto BUSCAR_SERIAL
if "%opcion%"=="0" goto MAIN_MENU

echo Opcion no valida.
pause
goto SUBMENU_DB

:CREAR_DB_LOCAL
echo.
echo [INFO] Creando/Verificando tablas en la base de datos local...
cd /d "%PROJECT_ROOT%"
"%VENV_PYTHON%" create_production_db.py
pause
goto SUBMENU_DB

:IMPORTAR_MASIVO
echo.
echo [INFO] Asegurando que 'pandas' y 'openpyxl' esten instalados...
"%VENV_PYTHON%" -m pip install pandas openpyxl >nul
cd /d "%PROJECT_ROOT%scripts\inventario"
if exist "importador_masivo_workmanager.py" (
    "%VENV_PYTHON%" importador_masivo_workmanager.py
    echo [OK] Importacion completada.
) else (
    echo [ERROR] No se encontro importador_masivo_workmanager.py
)
pause
goto SUBMENU_DB

:VERIFICAR_DB
echo.
echo [INFO] Verificando la base de datos y el conteo de registros...
"%VENV_PYTHON%" "%PROJECT_ROOT%scripts\verify_db.py"
pause
goto SUBMENU_DB

:BUSCAR_SERIAL
echo.
set "serial_a_buscar="
set /p "serial_a_buscar=Introduce el serial a buscar (o presiona Enter para cancelar): "
if not defined serial_a_buscar goto SUBMENU_DB

cd /d "%PROJECT_ROOT%"
"%VENV_PYTHON%" -c "import sqlite3, os, json; serial = os.environ.get('serial_a_buscar', ''); conn = sqlite3.connect('workmanager_erp.db'); conn.row_factory = sqlite3.Row; c = conn.cursor(); c.execute('SELECT * FROM equipos_individuales WHERE serial LIKE ?', ('%%' + serial + '%%',)); row = c.fetchone(); print(f'--- Resultado para \"{serial}\" ---'); print('Encontrado:' if row else 'No encontrado.'); print(json.dumps(dict(row), indent=2, ensure_ascii=False)) if row else ''"
pause
goto SUBMENU_DB

:BACKUP
cls
echo --- GESTOR DE COPIAS DE SEGURIDAD ---
call :PREPARAR_ENTORNO
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudo preparar el entorno. Abortando.
    pause
    goto MAIN_MENU
)

:SUBMENU_BACKUP
cls
color 0E
echo ================================================================
echo                 GESTOR DE COPIAS DE SEGURIDAD
echo ================================================================
echo 1. Crear copia de seguridad COMPLETA
echo 2. Crear copia de seguridad PARCIAL (tablas especificas)
echo.
echo 0. Volver al Menu Principal
echo.
set /p "opcion=Selecciona una opcion: "

if "%opcion%"=="1" ("%VENV_PYTHON%" "%PROJECT_ROOT%scripts\backup_manager.py" full)
if "%opcion%"=="2" (
    set /p "TABLES=Introduce los nombres de las tablas separados por espacios: "
    "%VENV_PYTHON%" "%PROJECT_ROOT%scripts\backup_manager.py" partial !TABLES!
)
if "%opcion%"=="0" goto MAIN_MENU

pause
goto MAIN_MENU

:MIGRATE_PROD_UNIFIED
cls
echo --- MIGRACION DE DATOS A PRODUCCION ---
call :PREPARAR_ENTORNO
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudo preparar el entorno. Abortando.
    pause
    goto MAIN_MENU
)

echo.
echo Este script copiara los datos de tu base de datos local (SQLite)
echo a tu base de datos de produccion (PostgreSQL, MariaDB, etc.).
echo.
echo ADVERTENCIA: Se recomienda ejecutarlo sobre una base de datos de produccion vacia.
echo.

set "DATABASE_URL="
echo Necesitaras la URL de conexion de tu base de datos de produccion.
echo Esta URL la proporciona tu proveedor de hosting (Vercel, Render, cPanel, etc.).
echo Ejemplo: postgresql://usuario:contrasena@host:puerto/basededatos
echo.
set /p "DATABASE_URL=Pega la URL de conexion externa aqui: "

if not defined DATABASE_URL (
    echo [ERROR] No se introdujo una URL. Abortando.
    pause
    goto MAIN_MENU
)

echo.
echo [INFO] Instalando dependencias necesarias para la migracion...
"%VENV_PYTHON%" -m pip install sqlalchemy pandas psycopg2-binary mysql-connector-python >nul

echo [INFO] Iniciando el script de migracion...
"%VENV_PYTHON%" "%PROJECT_ROOT%migrate.py"

echo.
echo [OK] Migracion finalizada.
pause
goto MAIN_MENU

:SYNC_AUTO
cls
echo --- INICIAR SINCRONIZACION AUTOMATICA ---
echo.
echo Se abrira una nueva ventana que vigilara tus archivos.
echo Cada vez que guardes un cambio, se subira automaticamente a GitHub.
echo Puedes minimizar esa ventana y seguir trabajando.
echo Para detener la sincronizacion, simplemente cierra la nueva ventana.
echo.
pause

start "Sincronizacion Automatica en Segundo Plano" cmd /c "%PROJECT_ROOT%start.bat" SYNC_LOOP
goto MAIN_MENU

:CLEAN_REPO
cls
call "%PROJECT_ROOT%limpiar_repositorio.bat"
goto MAIN_MENU

:FORCE_PUSH
cls
color 0C
echo --- FORZAR SINCRONIZACION CON GITHUB ---
echo.
echo ADVERTENCIA: Esta opcion sobreescribira el repositorio en GitHub con
echo tu version local. Usala solo si la opcion 4 falla repetidamente.
echo.
set /p "CONFIRM=Estas seguro de que quieres continuar? (s/n): "
if /i not "%CONFIRM%"=="s" (
    echo Accion cancelada.
    pause
    goto MAIN_MENU
)

echo.
echo [1/2] Guardando todos los cambios locales...
git add .
git commit -m "Forzando sincronizacion para corregir historial"
echo [2/2] Forzando la subida a GitHub (push --force)...
git push origin main --force
echo.
echo [OK] Sincronizacion forzada completada.
pause
goto MAIN_MENU

:GIT_PUSH
cls
echo --- PREPARAR PARA PRODUCCION (SUBIR A GITHUB) ---
echo.
echo Este asistente te ayudara a guardar tus cambios y subirlos a GitHub.
echo Esto es necesario para que servicios como Render puedan actualizar tu aplicacion.
echo.

git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git no esta instalado o no se encuentra en el PATH.
    echo Por favor, instala Git desde https://git-scm.com/download/win y reinicia la terminal.
    pause
    goto MAIN_MENU
)

REM --- Verificacion y configuracion del repositorio remoto ---
git remote -v | find "origin" >nul
if %errorlevel% neq 0 (
    echo [CONFIGURACION] No se ha encontrado un repositorio remoto de GitHub (origin).
    echo.
    echo Por favor, ve a tu pagina de GitHub, crea un repositorio y copia la URL HTTPS.
    echo Se vera algo como: https://github.com/TuUsuario/TuRepo.git
    echo.
    set /p "REPO_URL=Pega la URL de tu repositorio aqui y presiona Enter: "
    if not defined REPO_URL (
        echo [ERROR] No se introdujo una URL. Abortando.
        pause
        goto MAIN_MENU
    )
    git remote add origin "!REPO_URL!"
)

git status
echo.
set /p "COMMIT_MSG=Escribe un mensaje breve describiendo tus cambios: "
if not defined COMMIT_MSG set "COMMIT_MSG=Actualizacion de rutina"

echo.
echo [1/3] Guardando cambios locales (git add)...
git add .

echo [2/3] Creando punto de guardado (git commit)...
REM Usamos 'git diff-index' para ver si hay cambios. Si no hay, no intentamos hacer commit.
git diff-index --quiet HEAD -- || git commit -m "%COMMIT_MSG%"

echo [3/4] Sincronizando con cambios remotos (git pull --rebase)...
REM Usamos --rebase para aplicar tus cambios encima de los cambios remotos.
REM --autostash guarda temporalmente tus cambios si hay conflictos.
git pull origin main --rebase --autostash --allow-unrelated-histories --no-edit
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Hubo un conflicto al sincronizar con GitHub que no se pudo resolver automaticamente.
    echo Por favor, abre tu proyecto en un editor como VS Code para resolver los conflictos marcados.
    echo Una vez resueltos, ejecuta esta opcion de nuevo.
    pause
    goto MAIN_MENU
)

echo [4/4] Subiendo cambios a GitHub (git push)...
git push origin main
echo.
echo [OK] Proceso finalizado. Si no hubo errores, tus cambios estan en GitHub.
pause

cls
color 0E
echo ======================================================================
echo          PASO FINAL: INICIALIZAR BASE DE DATOS DE PRODUCCION
echo ======================================================================
echo.
echo Tu codigo ya esta en GitHub. Ahora, es probable que necesites
echo crear las tablas en tu base de datos de produccion (Vercel/Render).
echo.
set /p "INIT_PROD=Deseas inicializar la base de datos de produccion ahora? (s/n): "

if /i "%INIT_PROD%"=="s" (
    echo.
    echo Necesitaras la URL de conexion de tu base de datos de produccion.
    set /p "DATABASE_URL=Pega la URL de conexion externa aqui: "
    if defined DATABASE_URL (
        echo.
        echo [INFO] Ejecutando script de creacion de tablas en produccion...
        "%VENV_PYTHON%" create_production_db.py
    )
)
goto MAIN_MENU

:SYNC_LOOP
color 0E
echo ======================================================================
echo          WORKMANAGER ERP - MODO DE SINCRONIZACION AUTOMATICA
echo ======================================================================
echo.
echo Esta ventana esta vigilando tu proyecto.
echo Para detener, cierra esta ventana.
echo.

:WATCH_LOOP
echo.
echo [%time%] Vigilando cambios...
timeout /t 10 /nobreak >nul

git status --porcelain | findstr . >nul
if %errorlevel% equ 0 (
    echo [%time%] ! CAMBIOS DETECTADOS ! Iniciando sincronizacion...
    
    echo   - Sincronizando con el repositorio remoto (git pull)...
    git pull origin main --rebase --autostash --allow-unrelated-histories --no-edit
    
    echo   - Guardando cambios locales (git add)...
    git add .
    
    echo   - Creando punto de guardado (git commit)...
    git diff-index --quiet HEAD -- || git commit -m "Sincronizacion automatica - %date% %time%"
    
    echo   - Subiendo cambios a GitHub (git push)...
    git push origin main
    echo [%time%] [OK] Sincronizacion completada.
)
goto WATCH_LOOP

:PREPARAR_ENTORNO
py -3 --version >nul 2>&1 & if errorlevel 1 (echo [ERROR] Python 3 no esta instalado. & exit /b 1)
if not exist "%PROJECT_ROOT%.venv" (
    echo [INFO] Creando entorno virtual .venv (solo la primera vez)...
    py -3 -m venv "%PROJECT_ROOT%.venv" || (echo [ERROR] Fallo al crear .venv. & exit /b 1)
)
echo [INFO] Instalando/verificando dependencias...
set "PIP_EXE=%PROJECT_ROOT%.venv\Scripts\pip.exe"

"%PIP_EXE%" install -r "%PROJECT_ROOT%requirements.txt" >nul
if errorlevel 1 (
    echo [ERROR] Fallo al instalar dependencias base. Ejecutando de nuevo con mas detalles...
    "%PIP_EXE%" install -r "%PROJECT_ROOT%requirements.txt"
    pause
    exit /b 1
)

if exist "%PROJECT_ROOT%requirements-dev.txt" (
    "%PIP_EXE%" install -r "%PROJECT_ROOT%requirements-dev.txt" >nul
    if errorlevel 1 (
        echo [ERROR] Fallo al instalar dependencias de desarrollo. Ejecutando de nuevo con mas detalles...
        "%PIP_EXE%" install -r "%PROJECT_ROOT%requirements-dev.txt"
        pause
        exit /b 1
    )
)
exit /b 0
