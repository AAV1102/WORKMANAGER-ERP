from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import sqlite3
import os
import csv
from datetime import datetime

bajas_import_bp = Blueprint(
    "bajas_import",
    __name__,
    url_prefix="/bajas/import",
    template_folder="../templates"
)


def get_db_path():
    return os.path.join(current_app.root_path, "workmanager_erp.db")


def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def parse_date(value: str):
    """
    Intenta convertir la fecha del CSV a un formato YYYY-MM-DD.
    Si no puede, devuelve None.
    """
    if not value:
        return None
    v = value.strip()
    if not v:
        return None

    # Intentar algunos formatos comunes (puedes luego ajustarlos a tus fechas reales)
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(v, fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    return None


@bajas_import_bp.route("/", methods=["GET"])
def form_bajas():
    """
    Formulario para subir el CSV de equipos dados de baja.
    Puede ser Bajas.csv o Equipos Baja General.csv.
    """
    return render_template("import_bajas.html")


@bajas_import_bp.route("/", methods=["POST"])
def import_bajas():
    """
    Importa registros de bajas:
    - Lee archivo CSV (Bajas.csv o Equipos Baja General.csv)
    - Busca en equipos_individuales por PLACA / SERIAL
    - Si encuentra el equipo:
        * actualiza estado = 'baja'
        * disponible = 'No'
        * registra en inventario_bajas
    - Si NO encuentra, registra baja sin equipo_id (para revisar luego)
    """
    file = request.files.get("file")
    if not file or file.filename == "":
        flash("Debes seleccionar un archivo CSV de bajas.", "danger")
        return redirect(url_for("bajas_import.form_bajas"))

    upload_dir = os.path.join(current_app.root_path, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    file.save(filepath)

    updated_equipos = 0
    bajas_registradas = 0
    sin_coincidencia = 0
    errores = []

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Asegurar que la tabla inventario_bajas exista (tu app ya la crea en init_db)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS inventario_bajas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipo_id INTEGER,
                tipo_inventario TEXT,
                motivo_baja TEXT NOT NULL,
                fecha_baja TEXT DEFAULT CURRENT_TIMESTAMP,
                responsable_baja TEXT,
                documentos_soporte TEXT,
                fotografias_soporte TEXT,
                observaciones TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        with open(filepath, "r", encoding="latin1", newline="") as f:
            sample = f.read(4096)
            f.seek(0)
            delimiter = ";" if sample.count(";") > sample.count(",") else ","
            reader = csv.reader(f, delimiter=delimiter)
            rows = list(reader)

        if len(rows) < 2:
            flash("El archivo de bajas no tiene suficientes filas de datos.", "danger")
            return redirect(url_for("bajas_import.form_bajas"))

        header = [(h or "").strip().upper() for h in rows[0]]

        def idx(col_name):
            return header.index(col_name) if col_name in header else None

        # Tratamos de mapear columnas típicas
        idx_placa = idx("PLACA") or idx("PLACA EQUIPO")
        idx_serial = idx("SERIAL") or idx("SERIAL EQUIPO")
        idx_motivo = idx("MOTIVO BAJA") or idx("MOTIVO") or idx("CAUSA")
        idx_responsable = idx("RESPONSABLE BAJA") or idx("RESPONSABLE") or idx("USUARIO")
        idx_fecha = idx("FECHA BAJA") or idx("FECHA") or idx("FECHA REGISTRO")
        idx_observaciones = idx("OBSERVACIONES") if "OBSERVACIONES" in header else None

        for line_num, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue

            placa = row[idx_placa].strip() if idx_placa is not None and row[idx_placa] else None
            serial = row[idx_serial].strip() if idx_serial is not None and row[idx_serial] else None
            motivo_baja = row[idx_motivo].strip() if idx_motivo is not None and row[idx_motivo] else "BAJA SIN MOTIVO"
            responsable_baja = row[idx_responsable].strip() if idx_responsable is not None and row[idx_responsable] else None
            fecha_baja_raw = row[idx_fecha].strip() if idx_fecha is not None and row[idx_fecha] else None
            observaciones = row[idx_observaciones].strip() if idx_observaciones is not None and row[idx_observaciones] else None

            fecha_baja = parse_date(fecha_baja_raw) or datetime.now().strftime("%Y-%m-%d")

            equipo_id = None

            # Buscar primero por PLACA, luego por SERIAL
            if placa:
                cur.execute("""
                    SELECT id FROM equipos_individuales WHERE placa = ? LIMIT 1
                """, (placa,))
                eq = cur.fetchone()
                if eq:
                    equipo_id = eq["id"]
            if not equipo_id and serial:
                cur.execute("""
                    SELECT id FROM equipos_individuales WHERE serial = ? LIMIT 1
                """, (serial,))
                eq = cur.fetchone()
                if eq:
                    equipo_id = eq["id"]

            if equipo_id:
                # Cambiar estado del equipo a 'baja' y disponible = 'No'
                cur.execute("""
                    UPDATE equipos_individuales
                    SET estado = 'baja',
                        disponible = 'No',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (equipo_id,))
                updated_equipos += 1

                cur.execute("""
                    INSERT INTO inventario_bajas (
                        equipo_id, tipo_inventario, motivo_baja,
                        fecha_baja, responsable_baja, observaciones
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    equipo_id,
                    "individual",
                    motivo_baja,
                    fecha_baja,
                    responsable_baja,
                    observaciones
                ))
                bajas_registradas += 1
            else:
                # No encontró el equipo en inventario general: igual registramos baja,
                # pero con equipo_id = NULL para posterior revisión
                cur.execute("""
                    INSERT INTO inventario_bajas (
                        equipo_id, tipo_inventario, motivo_baja,
                        fecha_baja, responsable_baja, observaciones
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    None,
                    "desconocido",
                    motivo_baja,
                    fecha_baja,
                    responsable_baja,
                    f"(SIN COINCIDENCIA) {observaciones or ''}"
                ))
                sin_coincidencia += 1

        conn.commit()
        conn.close()

    except Exception as e:
        errores.append(str(e))

    # Mensajes para que sepas qué pasó
    if updated_equipos:
        flash(f"Equipos marcados como BAJA: {updated_equipos}.", "success")
    if bajas_registradas:
        flash(f"Registros de baja creados: {bajas_registradas}.", "info")
    if sin_coincidencia:
        flash(f"Bajas sin equipo encontrado en inventario: {sin_coincidencia}.", "warning")
    if errores:
        flash(f"Error en importación de bajas: {errores[0]}", "danger")

    return redirect(url_for("bajas.lista_bajas"))
