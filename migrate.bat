@echo off
chcp 65001 >nul
setlocal

set "PROJECT_ROOT=%~dp0"
set "VENV_PYTHON=%PROJECT_ROOT%.venv\Scripts\python.exe"

cls
color 0D
echo ======================================================================
echo           WORKMANAGER ERP - ASISTENTE DE MIGRACION DE DATOS
echo ======================================================================
echo.
echo Este script copiara los datos de tu base de datos local (SQLite)
echo a tu base de datos de produccion (PostgreSQL, MariaDB, etc.).
echo.
echo ADVERTENCIA: Este proceso es aditivo. Si una fila ya existe,
echo puede causar un error o duplicados. Se recomienda ejecutarlo
echo sobre una base de datos de produccion vacia.
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
    exit /b
)

echo.
echo [INFO] Instalando dependencias necesarias para la migracion...
"%VENV_PYTHON%" -m pip install sqlalchemy pandas psycopg2-binary mysql-connector-python >nul

echo [INFO] Iniciando el script de migracion...
"%VENV_PYTHON%" "%PROJECT_ROOT%migrate.py"

echo.
echo [OK] Migracion finalizada.
pause