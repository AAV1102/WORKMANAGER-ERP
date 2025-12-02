@echo off
chcp 65001 >nul
color 0A
setlocal

REM ===============================================================
REM WorkManager ERP - Lanzador completo
REM - Crea/activa .venv
REM - Instala requirements.txt
REM - (Opcional) ejecuta importador masivo
REM - Inicia app.py
REM ===============================================================

set "PROJECT_ROOT=%~dp0"
set "VENV_DIR=%PROJECT_ROOT%.venv"
set "PYTHON=%VENV_DIR%\Scripts\python.exe"
set "PIP=%VENV_DIR%\Scripts\pip.exe"
set "REQUIREMENTS=%PROJECT_ROOT%requirements.txt"
set "IMPORT_BAT=%PROJECT_ROOT%INSTALAR_INVENTARIO_MAESTRO.bat"

echo ===============================================================
echo WorkManager ERP - Lanzador Full
echo Ruta del proyecto: %PROJECT_ROOT%
echo ===============================================================
echo.

REM 0) Verificar si Python está instalado
py -3 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3 no parece estar instalado o no esta en el PATH.
    echo Por favor, instala Python 3 (desde python.org o la Microsoft Store) y asegurate de que este en el PATH.
    pause
    exit /b 1
)

REM 1) Crear entorno virtual si no existe
if not exist "%VENV_DIR%" (
    echo [1/4] Creando entorno virtual en .venv ...
    py -3 -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual. Verifica tu instalacion de Python.
        pause
        exit /b 1
    )
) else (
    echo [1/4] Entorno virtual ya existe.
)

REM 2) Actualizar pip e instalar requirements
echo.
echo [2/4] Actualizando pip e instalando requirements...
"%PYTHON%" -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo actualizar pip. Verifica el entorno virtual en la carpeta .venv.
    pause
    exit /b 1
)
if exist "%REQUIREMENTS%" (
    "%PIP%" install -r "%REQUIREMENTS%"
    if %errorlevel% neq 0 (
        echo [ERROR] Hubo un error instalando los paquetes de requirements.txt.
        pause
        exit /b 1
    )
) else (
    echo [WARN] No se encontro requirements.txt en %REQUIREMENTS%
)

REM 3) Opcional: Importador masivo
echo.
echo [3/4] Opciones:
echo   1) Ejecutar importador masivo (Inventario Maestro)
echo   2) Saltar e iniciar servidor Flask
set /p "CHOICE=Selecciona [1/2]: "
if "%CHOICE%"=="1" (
    if exist "%IMPORT_BAT%" (
        call "%IMPORT_BAT%"
    ) else (
        echo [WARN] No se encontro %IMPORT_BAT%. Se omite importador.
    )
)

REM 4) Iniciar Flask
echo.
echo [4/4] Iniciando servidor Flask (app.py) ...
cd /d "%PROJECT_ROOT%"
set FLASK_APP=app.py
set FLASK_ENV=development
"%PYTHON%" -m flask run

echo.
echo Servidor detenido.
pause
endlocal
exit /b
