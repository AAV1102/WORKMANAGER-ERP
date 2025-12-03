@echo off
chcp 65001 >nul
color 0C

echo ======================================================================
echo      WORKMANAGER ERP - SCRIPT DE LIMPIEZA PROFUNDA DE GITHUB
echo ======================================================================
echo.
echo ADVERTENCIA: Este proceso reescribira el historial de tu repositorio
echo para eliminar archivos grandes y solucionar errores de despliegue.
echo.
set /p "CONFIRM=Estas seguro de que quieres continuar? (s/n): "
if /i not "%CONFIRM%"=="s" (
    echo Accion cancelada.
    pause
    exit /b
)

REM --- Verificación de git-filter-repo ---
git-filter-repo --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] La herramienta 'git-filter-repo' no esta instalada.
    echo Por favor, abre una nueva terminal y ejecuta: pip install git-filter-repo
    echo Luego, vuelve a ejecutar este script.
    pause
    exit /b
)

echo.
echo [1/3] Guardando cambios locales pendientes (si los hay)...
git add .
git commit -m "Checkpoint antes de limpieza con filter-repo"

echo.
echo [2/3] Ejecutando limpieza profunda del historial con git-filter-repo...
echo      Esto puede tardar varios minutos.

REM Elimina carpetas completas del historial
git-filter-repo --path mingit --path INVENTARIOS --path uploads --path backups --path tmp_imports --invert-paths --force

REM Elimina archivos grandes que puedan haber quedado
git-filter-repo --strip-blobs-bigger-than 5M --force

echo.
echo [3/3] Forzando la subida del repositorio limpio a GitHub...
git push origin main --force

echo.
echo [OK] Limpieza definitiva completada. Tu repositorio ahora es mucho mas ligero.
echo      Intenta desplegar tu aplicacion en Vercel de nuevo.
pause