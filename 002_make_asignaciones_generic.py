import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'workmanager_erp.db')

def run_migration():
    """
    Añade la columna 'asset_type' a la tabla 'asignaciones' para hacerla universal.
    """
    if not os.path.exists(DB_PATH):
        print(f"Error: La base de datos '{DB_PATH}' no fue encontrada.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(asignaciones)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'asset_type' not in columns:
            print("Añadiendo columna 'asset_type' a la tabla 'asignaciones'...")
            # Añadimos la columna y por defecto asignamos el tipo 'equipos_tecnologicos' a los registros existentes.
            cursor.execute("ALTER TABLE asignaciones ADD COLUMN asset_type TEXT DEFAULT 'equipos_tecnologicos'")
            conn.commit()
            print("¡Columna 'asset_type' añadida exitosamente!")
        else:
            print("La columna 'asset_type' ya existe. No se necesita ninguna acción.")
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration()