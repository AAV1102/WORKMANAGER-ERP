@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"

cls
color 0E
echo ======================================================================
echo          WORKMANAGER ERP - MODO DE SINCRONIZACION AUTOMATICA
echo ======================================================================
echo.
echo Este script vigilara tu proyecto y subira los cambios a GitHub
echo automaticamente cada vez que guardes un archivo.
echo.
echo Puedes minimizar esta ventana y seguir trabajando.
echo Para detener, cierra esta ventana.
echo.
echo ======================================================================

REM --- Verificacion inicial de Git y configuracion remota ---
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Git no esta instalado. Por favor, instalalo y reinicia.
    pause
    exit /b
)

git remote -v | find "origin" >nul
if %errorlevel% neq 0 (
    echo [ERROR] El repositorio de GitHub no esta configurado.
    echo Ejecuta 'start.bat' y usa la opcion 4 para configurarlo por primera vez.
    pause
    exit /b
)

:WATCH_LOOP
echo.
echo [%time%] Vigilando cambios...

REM Espera 10 segundos antes de la proxima verificacion
timeout /t 10 /nobreak >nul

REM Verifica si hay archivos modificados o nuevos sin seguimiento
git status --porcelain | findstr . >nul
if %errorlevel% equ 0 (
    echo [%time%] ! CAMBIOS DETECTADOS ! Iniciando sincronizacion...
    
    echo   - Sincronizando con el repositorio remoto (git pull)...
    git pull origin main --rebase --autostash --allow-unrelated-histories
    
    echo   - Guardando cambios locales (git add)...
    git add .
    
    echo   - Creando punto de guardado (git commit)...
    git commit -m "Sincronizacion automatica - %date% %time%"
    
    echo   - Subiendo cambios a GitHub (git push)...
    git push origin main
    echo [%time%] [OK] Sincronizacion completada.
)

goto :WATCH_LOOP