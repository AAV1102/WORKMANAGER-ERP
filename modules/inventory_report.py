import os
import shutil
from datetime import datetime
import io
import pandas as pd
from flask import Blueprint, render_template, request, redirect, url_for, send_from_directory, flash, send_file
from werkzeug.utils import secure_filename

from modules.inventory_generator import generar_informe_inventario
from modules.db_utils import get_db_connection

inventory_report_bp = Blueprint("inventory_report", __name__, template_folder="../templates")

UPLOAD_ROOT = "uploads"
REPORTS_DIR = os.path.join("static", "reports")


def _ensure_dirs():
    os.makedirs(UPLOAD_ROOT, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)


@inventory_report_bp.route("/inventario/report", methods=["GET"])
def inventario_report_form():
    _ensure_dirs()
    return render_template("inventory_report_form.html")


@inventory_report_bp.route("/inventario/report", methods=["POST"])
def inventario_report_generate():
    _ensure_dirs()
    temp_dir = os.path.join(UPLOAD_ROOT, datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    os.makedirs(temp_dir, exist_ok=True)

    files = request.files.getlist("inventory_files")
    if not files:
        flash("No subiste archivos.", "danger")
        return redirect(url_for("inventory_report.inventario_report_form"))

    for f in files:
        if f.filename:
            fname = secure_filename(f.filename)
            f.save(os.path.join(temp_dir, fname))

    report_path, result = generar_informe_inventario(temp_dir, REPORTS_DIR)
    shutil.rmtree(temp_dir, ignore_errors=True)

    if isinstance(result, str):
        flash(result, "danger")
        return redirect(url_for("inventory_report.inventario_report_form"))

    report_name = os.path.basename(report_path)
    if isinstance(result, list):
        for stat in result:
            flash(
                f"[{stat['target']}] Insertados: {stat['inserted']}, Actualizados: {stat['updated']}, "
                f"Staging: {stat['staged']}, Errores: {len(stat['errors'])}",
                "info",
            )
    flash("Reporte generado con exito.", "success")
    return redirect(url_for("inventory_report.inventario_report_success", filename=report_name))


@inventory_report_bp.route("/inventario/report/success/<filename>")
def inventario_report_success(filename):
    return render_template("inventory_report_success.html", filename=filename)


@inventory_report_bp.route("/inventario/report/download/<filename>")
def inventario_report_download(filename):
    return send_from_directory(REPORTS_DIR, filename, as_attachment=True)


@inventory_report_bp.route("/inventario/report/db", methods=["GET"])
def inventario_report_db_view():
    """Vista rápida de tablas clave y enlaces de exportación desde la BD."""
    conn = get_db_connection()
    cursor = conn.cursor()
    tables = [
        "equipos_individuales",
        "licencias_office365",
        "empleados",
        "inventario_bajas",
        "insumos",
        "tandas_equipos_nuevos",
    ]
    stats = []
    for name in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {name}")
            count = cursor.fetchone()[0]
        except Exception:
            count = None
        stats.append({"table": name, "rows": count})
    conn.close()
    return render_template("inventory_report_db.html", stats=stats)


@inventory_report_bp.route("/inventario/report/db/export", methods=["GET"])
def inventario_report_db_export():
    """Exporta una tabla de la BD a Excel para descarga directa."""
    table = request.args.get("table", "equipos_individuales")
    conn = get_db_connection()
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    except Exception as e:
        conn.close()
        flash(f"No se pudo exportar la tabla {table}: {e}", "danger")
        return redirect(url_for("inventory_report.inventario_report_db_view"))
    conn.close()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=table[:28], index=False)
    output.seek(0)
    filename = f"{table}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

