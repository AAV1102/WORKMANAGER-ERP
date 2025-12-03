import os
import sqlite3
import psycopg2
import mysql.connector
from urllib.parse import urlparse

DEFAULT_DB_FILENAME = "workmanager_erp.db"
ACTIVE_DB_PATH_FILE = "active_db.txt"

def get_db_connection():
    # Render, Vercel, Heroku, etc., inyectan la URL de la BD en esta variable de entorno.
    db_url = os.environ.get("DATABASE_URL")

    if db_url:
        # Conexión a PostgreSQL en producción
        result = urlparse(db_url)
        scheme = result.scheme.lower()

        if 'postgres' in scheme:
            try:
                conn = psycopg2.connect(
                    dbname=result.path[1:],
                    user=result.username,
                    password=result.password,
                    host=result.hostname,
                    port=result.port
                )
            except Exception as e:
                print(f"Error conectando a PostgreSQL: {e}")
                raise e
        elif 'mysql' in scheme or 'mariadb' in scheme:
            try:
                conn = mysql.connector.connect(
                    host=result.hostname,
                    user=result.username,
                    password=result.password,
                    database=result.path[1:],
                    port=result.port
                )
            except Exception as e:
                print(f"Error conectando a MariaDB/MySQL: {e}")
                raise e
        else:
            raise ValueError(f"Esquema de base de datos no soportado: {scheme}")
    else:
        # Conexión a SQLite para desarrollo local
        db_path = load_active_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
    return conn

def load_active_db_path():
    """
    Carga la ruta de la base de datos activa.
    Prioriza workmanager_erp.db y luego una guardada, o devuelve workmanager_erp.db por defecto.
    """
    # Obtiene la ruta del directorio donde se encuentra db_utils.py (modules/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Asume que workmanager_erp.db está en la raíz del proyecto (un nivel arriba de 'modules')
    project_root = os.path.join(current_dir, '..')

    workmanager_db_full_path = os.path.join(project_root, DEFAULT_DB_FILENAME)

    # 1. Si workmanager_erp.db existe, úsala como predeterminada
    if os.path.exists(workmanager_db_full_path):
        return workmanager_db_full_path

    # 2. Si no existe, revisa si hay una ruta guardada en active_db.txt
    active_db_file_path = os.path.join(project_root, ACTIVE_DB_PATH_FILE)
    if os.path.exists(active_db_file_path):
        try:
            with open(active_db_file_path, 'r') as f:
                saved_path = f.read().strip()
            if os.path.exists(saved_path):
                return saved_path
        except Exception as e:
            print(f"Error leyendo active_db.txt: {e}")

    # 3. Si nada de lo anterior, devuelve workmanager_db_full_path.
    #    SQLite la creará al primer intento de conexión si no existe.
    return workmanager_db_full_path

def save_active_db_path(db_path):
    """
    Guarda la ruta de la base de datos activa en un archivo.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..')
    active_db_file_path = os.path.join(project_root, ACTIVE_DB_PATH_FILE)
    with open(active_db_file_path, 'w') as f:
        f.write(db_path)
    return db_path

def list_available_dbs():
    """
    Lista las bases de datos .db disponibles en el directorio raíz del proyecto y en modules/.
    """
    dbs = set() # Usar un set para evitar duplicados
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..')

    # Añadir workmanager_erp.db explícitamente
    dbs.add(os.path.join(project_root, DEFAULT_DB_FILENAME))

    # Buscar archivos .db en la raíz del proyecto
    for file in os.listdir(project_root):
        if file.endswith('.db'):
            dbs.add(os.path.join(project_root, file))

    # Buscar archivos .db dentro de la carpeta 'modules'
    for file in os.listdir(current_dir):
        if file.endswith('.db'):
            dbs.add(os.path.join(current_dir, file))
    
    # Convertir las rutas completas a nombres base para la UI, por ejemplo.
    # O puedes devolver las rutas completas si es lo que necesita el selector.
    # Para el propósito del login, que lista 'opciones', los nombres base son comunes.
    return sorted([os.path.basename(db) for db in dbs])