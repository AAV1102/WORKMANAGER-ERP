import sqlite3
import os

def verify_database():
    """
    Se conecta a la base de datos local SQLite y muestra el conteo de filas para tablas clave.
    """
    # La ruta al script es 'c:\...\WORKMANAGER ERP\scripts\verify_db.py'
    # El directorio del proyecto está dos niveles arriba.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(project_root, 'workmanager_erp.db')

    if not os.path.exists(db_path):
        print(f"[ERROR] La base de datos '{os.path.basename(db_path)}' NO fue encontrada.")
        return

    print(f"[OK] '{os.path.basename(db_path)}' encontrada.")
    print("--- Conteo de Registros ---")

    tables_to_check = ['equipos_individuales', 'equipos_agrupados', 'sedes', 'empleados', 'licencias_office365', 'inventario_administrativo', 'usuarios']

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            for table in tables_to_check:
                cursor.execute(f"SELECT count(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"{table+':':<30} {count:,}")
    except Exception as e:
        print(f"\n[ERROR] Ocurrió un error al consultar la base de datos: {e}")

if __name__ == "__main__":
    verify_database()