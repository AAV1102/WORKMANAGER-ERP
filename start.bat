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
echo  5. Salir
echo.
echo ======================================================================
echo.
set /p "CHOICE=Selecciona una opcion y presiona Enter: "

if "%CHOICE%"=="1" goto INICIAR_LOCAL
if "%CHOICE%"=="2" goto GESTIONAR_DB
if "%CHOICE%"=="3" goto BACKUP
if "%CHOICE%"=="4" goto GIT_PUSH
if "%CHOICE%"=="5" goto :EOF

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

git status
echo.
set /p "COMMIT_MSG=Escribe un mensaje breve describiendo tus cambios: "
if not defined COMMIT_MSG set "COMMIT_MSG=Actualizacion de rutina"

echo.
echo [1/3] Guardando cambios locales (git add)...
git add .
echo [2/3] Creando punto de guardado (git commit)...
git commit -m "%COMMIT_MSG%"
echo [3/3] Subiendo cambios a GitHub (git push)...
git push
echo.
echo [OK] Proceso finalizado. Tus cambios deberian estar en GitHub.
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