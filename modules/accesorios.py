from flask import Blueprint, render_template
import sqlite3
import os

accesorios_bp = Blueprint(
    "accesorios",
    __name__,
    url_prefix="/accesorios",
    template_folder="../templates"
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workmanager_erp.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@accesorios_bp.route("/")
def lista_accesorios():
    """
    Lista de periféricos y complementos (Accesorios / Periféricos).
    """
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
        SELECT a.*,
               e.codigo_barras_individual AS equipo_codigo,
               e.serial AS equipo_serial,
               e.marca AS equipo_marca,
               e.modelo AS equipo_modelo,
               e.tecnologia AS equipo_tecnologia
        FROM accesorios_perifericos a
        LEFT JOIN equipos_individuales e ON a.equipo_id = e.id
        ORDER BY a.fecha_asignacion DESC, a.nombre_parte ASC
    """)
    accesorios = c.fetchall()
    conn.close()

    return render_template("accesorios.html", accesorios=accesorios)
