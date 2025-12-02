from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import sqlite3
import os
import csv
from datetime import datetime

asignaciones_import_bp = Blueprint(
    "asignaciones_import",
    __name__,
    url_prefix="/asignaciones/import",
    template_folder="../templates"
)


def get_db_path():
    return os.path.join(current_app.root_path, "workmanager_erp.db")


def get_conn():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def parse_fecha(value: str):
    if not value:
        return None
    v = value.strip()
    if not v:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(v, fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    return None


@asignaciones_import_bp.route("/", methods=["GET"])
def form_import_asignaciones():
    return render_template("import_asignaciones.html")


@asignaciones_import_bp.route("/", methods=["POST"])
def procesar_import_asignaciones():
    """
    Importa Equipos Entregados.csv

    Estructura vista:
    NOMBRE, CIUDAD, PLACA, SERIAL, PESTAÑA, FECHA DE ENVIO, GUIA

    Lógica:
    - Busca equipo por PLACA y/o SERIAL.
    - Si encuentra:
        * Actualiza equipos_individuales:
            - estado = 'asignado'
            - disponible = 'No'
            - ciudad = CIUDAD
            - asignado_nuevo = NOMBRE
            - fecha = FECHA DE ENVIO
        * Inserta un registro en asignaciones_equipos.
    - Si no encuentra:
        * Inserta igual registro en asignaciones_equipos con equipo_id = NULL.
    """
    file = request.files.get("file")
    if not file or file.filename == "":
        flash("Debes seleccionar el archivo Equipos Entregados.csv", "danger")
        return redirect(url_for("asignaciones_import.form_import_asignaciones"))

    upload_dir = os.path.join(current_app.root_path, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    file.save(filepath)

    conn = get_conn()
    cur = conn.cursor()

    # Asegurar tabla historial
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

    asignados = 0
    sin_coincidencia = 0

    try:
        with open(filepath, "r", encoding="latin1", newline="") as f:
            sample = f.read(4096)
            f.seek(0)
            delimiter = ";" if sample.count(";") > sample.count(",") else ","
            reader = csv.reader(f, delimiter=delimiter)
            rows = list(reader)

        if len(rows) < 2:
            flash("El archivo Equipos Entregados.csv no tiene suficientes filas.", "danger")
            return redirect(url_for("asignaciones_import.form_import_asignaciones"))

        header = [(h or "").strip().upper() for h in rows[0]]

        def idx(name):
            return header.index(name) if name in header else None

        idx_nombre = idx("NOMBRE")
        idx_ciudad = idx("CIUDAD")
        idx_placa = idx("PLACA")
        idx_serial = idx("SERIAL")
        idx_pestaña = idx("PESTAÑA") if "PESTAÑA" in header else idx("PESTAÃ‘A ")
        idx_fecha = idx("FECHA DE ENVIO") if "FECHA DE ENVIO" in header else idx("FECHA ENVIO")
        idx_guia = idx("GUIA") if "GUIA" in header else None

        for row in rows[1:]:
            if not any(row):
                continue

            nombre = row[idx_nombre].strip() if idx_nombre is not None and idx_nombre < len(row) else None
            ciudad = row[idx_ciudad].strip() if idx_ciudad is not None and idx_ciudad < len(row) else None
            placa = row[idx_placa].strip() if idx_placa is not None and idx_placa < len(row) else None
            serial = row[idx_serial].strip() if idx_serial is not None and idx_serial < len(row) else None
            pestaña = row[idx_pestaña].strip() if idx_pestaña is not None and idx_pestaña < len(row) else None
            fecha_raw = row[idx_fecha].strip() if idx_fecha is not None and idx_fecha < len(row) else None
            guia = row[idx_guia].strip() if idx_guia is not None and idx_guia < len(row) else None

            fecha_envio = parse_fecha(fecha_raw) or datetime.now().strftime("%Y-%m-%d")

            equipo_id = None

            # Buscar por placa
            if placa:
                cur.execute("SELECT id FROM equipos_individuales WHERE placa = ? LIMIT 1", (placa,))
                eq = cur.fetchone()
                if eq:
                    equipo_id = eq["id"]

            # Buscar por serial si no se encontró por placa
            if not equipo_id and serial:
                cur.execute("SELECT id FROM equipos_individuales WHERE serial = ? LIMIT 1", (serial,))
                eq = cur.fetchone()
                if eq:
                    equipo_id = eq["id"]

            # Insertar en historial
            cur.execute("""
                INSERT INTO asignaciones_equipos (
                    equipo_id, nombre_destino, ciudad_destino,
                    pestaña_origen, fecha_envio, guia, observaciones
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (equipo_id, nombre, ciudad, pestaña, fecha_envio, guia, None))

            # Actualizar inventario general si encontramos equipo
            if equipo_id:
                cur.execute("""
                    UPDATE equipos_individuales
                    SET estado = 'asignado',
                        disponible = 'No',
                        ciudad = COALESCE(?, ciudad),
                        asignado_nuevo = COALESCE(?, asignado_nuevo),
                        fecha = COALESCE(?, fecha),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (ciudad, nombre, fecha_envio, equipo_id))
                asignados += 1
            else:
                sin_coincidencia += 1

        conn.commit()
        flash(f"Equipos marcados como ASIGNADOS: {asignados}", "success")
        if sin_coincidencia:
            flash(f"Registros sin coincidencia en inventario: {sin_coincidencia}", "warning")

    except Exception as e:
        conn.rollback()
        flash(f"Error al importar asignaciones: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for("asignaciones.lista_asignaciones"))
