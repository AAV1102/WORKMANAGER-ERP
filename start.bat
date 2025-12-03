@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:MENU
cls
color 0A
echo ======================================================================
echo                 WORKMANAGER ERP - CENTRO DE CONTROL
echo ======================================================================
echo.
echo  1. Iniciar Servidor de Desarrollo (Local)
echo  2. Gestionar Base de Datos (Crear, Importar, Verificar...)
echo  3. Realizar Copia de Seguridad (Backup)
echo  4. Subir Cambios a GitHub (Preparar para Produccion)
echo  5. Iniciar Sincronizacion Automatica (Modo Vigilante)
echo.
echo  9. Forzar Sincronizacion con GitHub (SOLO SI HAY PROBLEMAS)
echo  0. Salir
echo.
echo ======================================================================
echo.
set /p "CHOICE=Selecciona una opcion y presiona Enter: "

if "%CHOICE%"=="1" goto INICIAR_LOCAL
if "%CHOICE%"=="2" goto GESTIONAR_DB
if "%CHOICE%"=="3" goto BACKUP
if "%CHOICE%"=="4" goto GIT_PUSH
if "%CHOICE%"=="5" goto SYNC_AUTO
if "%CHOICE%"=="9" goto FORCE_PUSH
if "%CHOICE%"=="0" goto :EOF

echo Opcion no valida.
pause
goto MENU

:INICIAR_LOCAL
cls
echo --- INICIANDO SERVIDOR DE DESARROLLO ---
call :PREPARAR_ENTORNO
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudo preparar el entorno. Abortando.
    pause
    goto MENU
)

echo.
echo [OK] Entorno listo. Iniciando servidor Flask...
set "PYTHON=%PROJECT_ROOT%.venv\Scripts\python.exe"
"%PYTHON%" "%PROJECT_ROOT%run.py"

echo.
echo Servidor detenido.
pause
goto MENU

:GESTIONAR_DB
cls
echo --- GESTION DE BASE DE DATOS ---
call :PREPARAR_ENTORNO
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudo preparar el entorno. Abortando.
    pause
    goto MENU
)

call "%PROJECT_ROOT%INSTALAR_INVENTARIO_MAESTRO.bat"
goto MENU

:BACKUP
cls
echo --- GESTOR DE COPIAS DE SEGURIDAD ---
call :PREPARAR_ENTORNO
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] No se pudo preparar el entorno. Abortando.
    pause
    goto MENU
)

call "%PROJECT_ROOT%backup.bat"
goto MENU

:SYNC_AUTO
cls
start "Sincronizacion Automatica" "%PROJECT_ROOT%sync_automatico.bat"
goto MENU

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
    goto MENU
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
goto MENU

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
    goto MENU
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
        goto MENU
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

echo [3/4] Sincronizando con cambios remotos (git pull)...
REM Se cambia a un merge normal en lugar de rebase para evitar que se detenga en conflictos complejos.
git pull origin main --no-rebase --allow-unrelated-histories --no-edit
echo [4/4] Subiendo cambios a GitHub (git push)...
git push
echo.
echo [OK] Proceso finalizado. Si no hubo errores, tus cambios estan en GitHub.
echo      Si ves un error de "merge", cierra esta ventana y abre una nueva para resolverlo.
pause
goto MENU

:PREPARAR_ENTORNO
set "PROJECT_ROOT=%~dp0"
py -3 --version >nul 2>&1 & if errorlevel 1 (echo [ERROR] Python 3 no esta instalado. & exit /b 1)
if not exist "%PROJECT_ROOT%.venv" (
    echo [INFO] Creando entorno virtual .venv (solo la primera vez)...
    py -3 -m venv "%PROJECT_ROOT%.venv" || (echo [ERROR] Fallo al crear .venv. & exit /b 1)
)
echo [INFO] Instalando/verificando dependencias de requirements.txt...
set "PIP_INSTALL=%PROJECT_ROOT%.venv\Scripts\pip.exe install -r %PROJECT_ROOT%requirements.txt"
%PIP_INSTALL% >nul
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al instalar dependencias. Ejecutando de nuevo con mas detalles... & %PIP_INSTALL% & pause & exit /b 1
)
exit /b 0