from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import sqlite3
import os
from datetime import datetime

asignaciones_bp = Blueprint(
    "asignaciones",
    __name__,
    url_prefix="/asignaciones",
    template_folder="../templates"
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workmanager_erp.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@asignaciones_bp.route("/")
def lista_asignaciones():
    """
    Historial de equipos entregados / asignados (Equipos Entregados.csv)
    """
    conn = get_db_connection()
    cur = conn.cursor()
    search_query = request.args.get('q', '')

    # Asegurar tabla historial asignaciones
    cur.execute("""
        CREATE TABLE IF NOT EXISTS asignaciones_equipos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo_id INTEGER,
            nombre_destino TEXT,
            ciudad_destino TEXT,
            pestaña_origen TEXT,
            fecha_envio TEXT,
            guia TEXT,
            observaciones TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    query = """
        SELECT a.*,
               e.codigo_barras_individual AS codigo_equipo,
               e.placa AS placa,
               e.serial AS serial,
               e.marca AS marca,
               e.modelo AS modelo,
               e.tecnologia AS tecnologia,
               e.asignado_nuevo AS asignado_actual,
               e.ciudad AS ciudad_actual,
               e.area AS area_actual
        FROM asignaciones_equipos a
        LEFT JOIN equipos_individuales e ON e.id = a.equipo_id
    """
    params = []
    if search_query:
        like_query = f"%{search_query}%"
        query += """
            WHERE LOWER(e.placa) LIKE LOWER(?) OR
                  LOWER(e.serial) LIKE LOWER(?) OR
                  LOWER(a.nombre_destino) LIKE LOWER(?) OR
                  LOWER(a.ciudad_destino) LIKE LOWER(?)
        """
        params.extend([like_query] * 4)

    query += " ORDER BY a.fecha_envio DESC, a.id DESC"
    cur.execute(query, params)
    asignaciones = cur.fetchall()
    conn.close()

    return render_template("asignaciones.html", asignaciones=asignaciones, search_query=search_query)

@asignaciones_bp.route("/api/search")
def api_search_asignaciones():
    conn = get_db_connection()
    cur = conn.cursor()
    search_query = request.args.get('q', '')

    query = """
        SELECT a.*,
               e.codigo_barras_individual AS codigo_equipo,
               e.placa AS placa,
               e.serial AS serial,
               e.marca AS marca,
               e.modelo AS modelo,
               e.tecnologia AS tecnologia,
               e.asignado_nuevo AS asignado_actual,
               e.ciudad AS ciudad_actual,
               e.area AS area_actual
        FROM asignaciones_equipos a
        LEFT JOIN equipos_individuales e ON e.id = a.equipo_id
    """
    params = []
    if search_query:
        like_query = f"%{search_query}%"
        query += """
            WHERE LOWER(e.placa) LIKE LOWER(?) OR
                  LOWER(e.serial) LIKE LOWER(?) OR
                  LOWER(a.nombre_destino) LIKE LOWER(?) OR
                  LOWER(a.ciudad_destino) LIKE LOWER(?)
        """
        params.extend([like_query] * 4)

    query += " ORDER BY a.fecha_envio DESC, a.id DESC"
    cur.execute(query, params)
    asignaciones = [dict(row) for row in cur.fetchall()]
    conn.close()

    return jsonify(asignaciones)
