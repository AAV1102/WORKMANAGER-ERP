from flask import Blueprint, render_template
import sqlite3
import os

bajas_bp = Blueprint(
    "bajas",
    __name__,
    url_prefix="/bajas",
    template_folder="../templates"
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workmanager_erp.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@bajas_bp.route("/")
def lista_bajas():
    """
    Lista de equipos dados de baja.
    Se apoya en la tabla inventario_bajas y trata de mostrar info del equipo.
    """
    conn = get_db_connection()
    c = conn.cursor()

    # Intentar unir con equipos_individuales usando equipo_id si coincide
    # Nota: en tu esquema original inventario_bajas referencia 'equipos',
    # pero aquí usaremos equipo_id apuntando a equipos_individuales.id
    c.execute("""
        SELECT b.*,
               e.codigo_barras_individual AS equipo_codigo,
               e.serial AS equipo_serial,
               e.marca AS equipo_marca,
               e.modelo AS equipo_modelo,
               e.tecnologia AS equipo_tecnologia,
               e.placa AS equipo_placa
        FROM inventario_bajas b
        LEFT JOIN equipos_individuales e ON b.equipo_id = e.id
        ORDER BY b.fecha_baja DESC, b.id DESC
    """)
    bajas = c.fetchall()
    conn.close()

    return render_template("bajas.html", bajas=bajas)
