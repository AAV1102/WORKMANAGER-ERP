import sqlite3
import os

def get_db_connection():
    """Conecta a la base de datos workmanager_erp.db"""
    db_path = os.path.join(os.path.dirname(__file__), 'workmanager_erp.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
