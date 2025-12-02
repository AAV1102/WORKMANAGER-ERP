@echo off
chcp 65001 >nul
color 0B
setlocal

REM ===============================================================
REM WorkManager ERP - Gestor de Copias de Seguridad
REM ===============================================================

set "PROJECT_ROOT=%~dp0"
set "VENV_PYTHON=%PROJECT_ROOT%.venv\Scripts\python.exe"
set "BACKUP_SCRIPT=%PROJECT_ROOT%scripts\backup_manager.py"

echo ===============================================================
echo Gestor de Copias de Seguridad - WorkManager ERP
echo ===============================================================
echo.

if not exist "%VENV_PYTHON%" (
    echo [ERROR] No se encuentra el entorno virtual.
    echo Por favor, ejecuta RUN_WORKMANAGER_FULL.bat al menos una vez para crearlo.
    pause
    exit /b 1
)

echo Opciones de copia de seguridad:
echo   1. Backup COMPLETO (Toda la base de datos)
echo   2. Backup PARCIAL (Solo tablas de inventario principal)
echo   3. Salir
echo.
set /p "CHOICE=Selecciona una opcion [1-3]: "

if "%CHOICE%"=="1" (
    "%VENV_PYTHON%" "%BACKUP_SCRIPT%" full
) else if "%CHOICE%"=="2" (
    "%VENV_PYTHON%" "%BACKUP_SCRIPT%" partial equipos_individuales equipos_agrupados sedes empleados
) else (
    echo Operacion cancelada.
)

echo.
echo Proceso finalizado.
pause
endlocal
exit /b