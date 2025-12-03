import os
import sys
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from create_production_db import create_tables, get_db_connection as get_prod_db_connection

def migrate_data():
    """
    Migra datos desde una base de datos SQLite local a una base de datos
    de producción (PostgreSQL o MySQL) definida por la variable de entorno DATABASE_URL.
    """
    print("=============================================")
    print("== INICIANDO MIGRACIÓN DE DATOS A PRODUCCIÓN ==")
    print("=============================================")

    # Cargar la variable DATABASE_URL desde un archivo .env si existe
    load_dotenv()
    prod_db_url = os.environ.get("DATABASE_URL")
    
    # El script migrate.bat establece esta variable de entorno.
    # Si no está, es un error.
    if not prod_db_url:
        prod_db_url = os.environ.get("DATABASE_URL_MIGRATE")

    if not prod_db_url:
        print("\n[ERROR] La variable de entorno DATABASE_URL no está configurada.")
        print("Asegúrate de que el script que llama a este archivo la haya definido.")
        sys.exit(1)

    # --- Configuración de las bases de datos ---
    local_db_path = os.path.join(os.path.dirname(__file__), 'workmanager_erp.db')
    local_engine = create_engine(f'sqlite:///{local_db_path}')
    
    # SQLAlchemy necesita que la URL de postgres sea 'postgresql'
    if prod_db_url.startswith("postgres://"):
        prod_db_url = prod_db_url.replace("postgres://", "postgresql://", 1)
        
    prod_engine = create_engine(prod_db_url)

    # --- Verificación y creación de tablas en producción ---
    print("\nVerificando esquema de la base de datos de producción...")
    prod_conn, db_type = get_prod_db_connection()
    if prod_conn:
        create_tables(prod_conn, db_type)
        prod_conn.close()
    # ----------------------------------------------------

    # --- Lista de tablas a migrar ---
    # El orden puede ser importante si hay claves foráneas.
    # Primero las tablas sin dependencias, luego las que dependen de ellas.
    tables_to_migrate = [
        'sedes',
        'usuarios',
        'empleados',
        'equipos_agrupados',
        'equipos_individuales',
        'notificaciones'
        # Añade aquí otras tablas que necesites migrar
    ]

    print(f"\nSe intentarán migrar {len(tables_to_migrate)} tablas.")

    for table_name in tables_to_migrate:
        try:
            print(f"  - Migrando tabla '{table_name}'...", end="")
            # Leer datos de SQLite
            df = pd.read_sql_table(table_name, local_engine)
            
            # Escribir datos a PostgreSQL
            # 'append' añade los datos. Si la tabla ya tiene datos, no los borra.
            df.to_sql(table_name, prod_engine, if_exists='append', index=False)
            
            print(f" OK ({len(df)} filas)")
        except Exception as e:
            print(f" FALLÓ. Error: {e}")

    print("\n[INFO] Proceso de migración finalizado.")

if __name__ == "__main__":
    migrate_data()