import sqlite3
import os
import time
import sys

def get_project_root():
    """Navega hacia arriba para encontrar la raíz del proyecto."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def backup_full(db_path, backup_dir):
    """Crea una copia de seguridad completa y segura de la base de datos."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"workmanager_erp_FULL_{timestamp}.db")
    
    print(f"[INFO] Iniciando copia de seguridad COMPLETA a '{backup_path}'...")
    try:
        source_conn = sqlite3.connect(db_path)
        backup_conn = sqlite3.connect(backup_path)
        with backup_conn:
            source_conn.backup(backup_conn, pages=1, progress=lambda s, r, t: print(f"  Copiando... {round((t-r)/t*100)}%", end='\r'))
        print("\n[SUCCESS] Copia de seguridad completa finalizada.")
    except sqlite3.Error as e:
        print(f"\n[FATAL] Error durante la copia de seguridad completa: {e}")
    finally:
        if 'source_conn' in locals(): source_conn.close()
        if 'backup_conn' in locals(): backup_conn.close()

def backup_partial(db_path, backup_dir, tables_to_backup):
    """Crea una copia de seguridad de tablas específicas."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"workmanager_erp_PARTIAL_{timestamp}.db")

    print(f"[INFO] Iniciando copia de seguridad PARCIAL a '{backup_path}'...")
    print(f"[INFO] Tablas a incluir: {', '.join(tables_to_backup)}")

    try:
        source_conn = sqlite3.connect(db_path)
        source_cursor = source_conn.cursor()
        
        backup_conn = sqlite3.connect(backup_path)
        backup_cursor = backup_conn.cursor()

        for table_name in tables_to_backup:
            print(f"  - Procesando tabla '{table_name}'...")
            # Obtener el esquema de la tabla
            source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            create_table_sql = source_cursor.fetchone()
            if not create_table_sql:
                print(f"    [WARN] La tabla '{table_name}' no existe en la base de datos de origen. Omitiendo.")
                continue
            
            # Crear la tabla en el backup
            backup_cursor.execute(create_table_sql[0])

            # Copiar los datos
            source_cursor.execute(f"SELECT * FROM {table_name}")
            rows = source_cursor.fetchall()
            if rows:
                placeholders = ','.join(['?'] * len(rows[0]))
                backup_cursor.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", rows)
        
        backup_conn.commit()
        print("[SUCCESS] Copia de seguridad parcial finalizada.")

    except sqlite3.Error as e:
        print(f"\n[FATAL] Error durante la copia de seguridad parcial: {e}")
        if 'backup_conn' in locals(): backup_conn.rollback()
    finally:
        if 'source_conn' in locals(): source_conn.close()
        if 'backup_conn' in locals(): backup_conn.close()

def main():
    if len(sys.argv) < 2:
        print("[ERROR] Modo de backup no especificado. Use 'full' o 'partial'.")
        sys.exit(1)

    project_root = get_project_root()
    db_path = os.path.join(project_root, 'workmanager_erp.db')
    backup_dir = os.path.join(project_root, 'backups')

    if not os.path.exists(db_path):
        print(f"[ERROR] La base de datos no existe en: {db_path}")
        return

    if not os.path.exists(backup_dir):
        print(f"[INFO] Creando directorio de backups: {backup_dir}")
        os.makedirs(backup_dir)

    mode = sys.argv[1]
    if mode == 'full':
        backup_full(db_path, backup_dir)
    elif mode == 'partial':
        if len(sys.argv) < 3:
            print("[ERROR] Para el modo parcial, debe especificar al menos una tabla.")
            sys.exit(1)
        tables = sys.argv[2:]
        backup_partial(db_path, backup_dir, tables)
    else:
        print(f"[ERROR] Modo '{mode}' no reconocido. Use 'full' o 'partial'.")

if __name__ == '__main__':
    main()