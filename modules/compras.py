from flask import Blueprint, render_template, request
import sqlite3
import os

compras_bp = Blueprint(
    "compras",
    __name__,
    url_prefix="/compras",
    template_folder="../templates"
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workmanager_erp.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@compras_bp.route("/")
def lista_compras():
    """
    Lista de compras registradas desde Compra Articulos.csv
    """
    conn = get_db_connection()
    cur = conn.cursor()
    search_query = request.args.get('q', '')

    # Aseguramos tabla de compras
    cur.execute("""
        CREATE TABLE IF NOT EXISTS compras_articulos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nit TEXT,
            entidad TEXT,
            ciudad TEXT,
            articulo TEXT,
            cantidad INTEGER,
            fecha TEXT,
            equipo_id INTEGER,
            serial_equipo TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    query = """
        SELECT c.*,
               e.codigo_barras_individual AS codigo_equipo,
               e.marca AS marca_equipo,
               e.modelo AS modelo_equipo,
               e.tecnologia AS tecnologia_equipo
        FROM compras_articulos c
        LEFT JOIN equipos_individuales e ON e.id = c.equipo_id
    """
    params = []
    if search_query:
        like_query = f"%{search_query}%"
        query += """
            WHERE LOWER(c.articulo) LIKE LOWER(?) OR
                  LOWER(c.entidad) LIKE LOWER(?) OR
                  LOWER(c.ciudad) LIKE LOWER(?) OR
                  LOWER(c.nit) LIKE LOWER(?)
        """
        params.extend([like_query] * 4)

    query += " ORDER BY c.id DESC"

    cur.execute(query, params)
    compras = cur.fetchall()
    conn.close()

    return render_template("compras.html", compras=compras, search_query=search_query)
