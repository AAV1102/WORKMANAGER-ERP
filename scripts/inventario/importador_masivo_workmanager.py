import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from modules.inventory_generator import generar_informe_inventario  # noqa: E402


def main():
    uploads_dir = os.path.join(PROJECT_ROOT, "uploads")
    reports_dir = os.path.join(PROJECT_ROOT, "static", "reports")
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    print("=" * 70)
    print("Importador masivo WorkManager ERP")
    print(f"Origen de archivos: {uploads_dir}")
    print(f"BD: workmanager_erp.db | Reportes: {reports_dir}")
    print("=" * 70)

    report_path, stats_or_error = generar_informe_inventario(uploads_dir, reports_dir)
    if isinstance(stats_or_error, str):
        print(f"[ERROR] {stats_or_error}")
        sys.exit(1)

    print("[OK] Importación completada.")
    if isinstance(stats_or_error, list):
        for stat in stats_or_error:
            print(
                f" - {stat['target']}: insertados={stat['inserted']}, "
                f"actualizados={stat['updated']}, staging={stat['staged']}, "
                f"errores={len(stat['errors'])}"
            )
    if report_path:
        print(f"Reporte generado: {report_path}")
    print(f"Finalizado: {datetime.now()}")


if __name__ == "__main__":
    main()
