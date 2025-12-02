from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import sqlite3
import os
import csv
from datetime import datetime

compras_import_bp = Blueprint(
    "compras_import",
    __name__,
    url_prefix="/compras/import",
    template_folder="../templates"
)


def get_db_path():
    return os.path.join(current_app.root_path, "workmanager_erp.db")


def get_conn():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


@compras_import_bp.route("/", methods=["GET"])
def form_import_compras():
    return render_template("import_compras.html")


@compras_import_bp.route("/", methods=["POST"])
def procesar_import_compras():
    """
    Importa Compra Articulos.csv

    Estructura actual:
    NIT, ENTIDAD, CIUDAD, ARTIUCULOS, CANTIDAD, FECHA

    Además:
    - Si en el futuro el archivo trae SERIAL o PLACA, se intenta vincular con equipos_individuales.
    """
    file = request.files.get("file")
    if not file or file.filename == "":
        flash("Debes seleccionar el archivo Compra Articulos.csv", "danger")
        return redirect(url_for("compras_import.form_import_compras"))

    upload_dir = os.path.join(current_app.root_path, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    file.save(filepath)

    conn = get_conn()
    cur = conn.cursor()

    # Asegurar tabla
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

    insertados = 0
    vinculados = 0

    try:
        with open(filepath, "r", encoding="latin1", newline="") as f:
            sample = f.read(4096)
            f.seek(0)
            delimiter = ";" if sample.count(";") > sample.count(",") else ","
            reader = csv.reader(f, delimiter=delimiter)
            rows = list(reader)

        if len(rows) < 2:
            flash("El archivo de compras no tiene suficientes filas.", "danger")
            return redirect(url_for("compras_import.form_import_compras"))

        header = [(h or "").strip().upper() for h in rows[0]]

        def idx(name):
            return header.index(name) if name in header else None

        idx_nit = idx("NIT")
        idx_entidad = idx("ENTIDAD")
        idx_ciudad = idx("CIUDAD")
        idx_articulo = idx("ARTIUCULOS") if "ARTIUCULOS" in header else idx("ARTICULOS")
        idx_cantidad = idx("CANTIDAD")
        idx_fecha = idx("FECHA")

        # Opcionales por si a futuro agregas serial/placa en el reporte
        idx_serial = idx("SERIAL") if "SERIAL" in header else None
        idx_placa = idx("PLACA") if "PLACA" in header else None

        for row in rows[1:]:
            if not any(row):
                continue

            nit = row[idx_nit].strip() if idx_nit is not None and idx_nit < len(row) else None
            entidad = row[idx_entidad].strip() if idx_entidad is not None and idx_entidad < len(row) else None
            ciudad = row[idx_ciudad].strip() if idx_ciudad is not None and idx_ciudad < len(row) else None
            articulo = row[idx_articulo].strip() if idx_articulo is not None and idx_articulo < len(row) else None

            cantidad = 0
            if idx_cantidad is not None and idx_cantidad < len(row):
                try:
                    cantidad = int((row[idx_cantidad] or "0").strip())
                except Exception:
                    cantidad = 0

            fecha_raw = row[idx_fecha].strip() if idx_fecha is not None and idx_fecha < len(row) else None
            fecha = fecha_raw or datetime.now().strftime("%Y-%m-%d")

            serial_equipo = None
            equipo_id = None

            if idx_serial is not None and idx_serial < len(row) and row[idx_serial]:
                serial_equipo = row[idx_serial].strip()
            elif idx_placa is not None and idx_placa < len(row) and row[idx_placa]:
                serial_equipo = row[idx_placa].strip()

            # Si hay algo que parezca serial/placa, intentamos vincularlo
            if serial_equipo:
                # Buscar por serial
                cur.execute("SELECT id FROM equipos_individuales WHERE serial = ? LIMIT 1", (serial_equipo,))
                eq = cur.fetchone()
                if not eq:
                    # Probar por placa
                    cur.execute("SELECT id FROM equipos_individuales WHERE placa = ? LIMIT 1", (serial_equipo,))
                    eq = cur.fetchone()

                if eq:
                    equipo_id = eq["id"]
                    vinculados += 1

            cur.execute("""
                INSERT INTO compras_articulos (
                    nit, entidad, ciudad, articulo, cantidad,
                    fecha, equipo_id, serial_equipo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nit, entidad, ciudad, articulo, cantidad, fecha, equipo_id, serial_equipo))
            insertados += 1

        conn.commit()
        flash(f"Compras registradas: {insertados}", "success")
        if vinculados:
            flash(f"Compras vinculadas a equipos del inventario: {vinculados}", "info")

    except Exception as e:
        conn.rollback()
        flash(f"Error al importar compras: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for("compras.lista_compras"))
