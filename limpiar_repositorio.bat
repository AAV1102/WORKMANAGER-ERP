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

echo.
echo [1/3] Eliminando la carpeta 'mingit' del historial...
git filter-branch --force --index-filter "git rm -r --cached --ignore-unmatch mingit" --prune-empty --tag-name-filter cat -- --all

echo.
echo [2/3] Eliminando la carpeta 'INVENTARIOS' del historial...
git filter-branch --force --index-filter "git rm -r --cached --ignore-unmatch INVENTARIOS" --prune-empty --tag-name-filter cat -- --all

echo.
echo [3/3] Forzando la subida del repositorio limpio a GitHub...
git push origin main --force

echo.
echo [OK] Limpieza completada. Tu repositorio ahora es mucho mas ligero.
echo      Intenta desplegar tu aplicacion en Vercel de nuevo.
pause