from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
from datetime import datetime, timezone

mantenimientos_bp = Blueprint(
    "mantenimientos",
    __name__,
    url_prefix="/mantenimientos",
    template_folder="../templates",
    static_folder="../static",
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workmanager_erp.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _fetch_equipo_display(equipo_id, tipo):
    conn = get_conn()
    c = conn.cursor()
    if tipo == "agrupado":
        row = c.execute("SELECT id, codigo_barras_unificado, descripcion_general FROM equipos_agrupados WHERE id=?", (equipo_id,)).fetchone()
        if row:
            return f"AGR-{row['id']} | {row['codigo_barras_unificado']} | {row['descripcion_general'] or ''}".strip()
    else:
        row = c.execute("SELECT id, codigo_barras_individual, placa, marca, modelo FROM equipos_individuales WHERE id=?", (equipo_id,)).fetchone()
        if row:
            return f"IND-{row['id']} | {row['codigo_barras_individual'] or row['placa'] or ''} | {row['marca'] or ''} {row['modelo'] or ''}".strip()
    return "Equipo no encontrado"


@mantenimientos_bp.route("/", methods=["GET"])
def dashboard():
    """Dashboard de mantenimientos con resumen y listado."""
    conn = get_conn()
    c = conn.cursor()

    c.execute(
        """
        SELECT m.*, 
               (SELECT tecnologia FROM equipos_individuales ei WHERE ei.id = m.equipo_id) AS tecnologia,
               (SELECT estado FROM equipos_individuales ei WHERE ei.id = m.equipo_id) AS estado_equipo
        FROM mantenimientos m
        ORDER BY datetime(m.created_at) DESC
        """
    )
    mantenimientos = [dict(row) for row in c.fetchall()]

    # Stats
    stats = {
        "total": len(mantenimientos),
        "pendientes": sum(1 for m in mantenimientos if (m.get("estado") or "pendiente") == "pendiente"),
        "en_progreso": sum(1 for m in mantenimientos if (m.get("estado") or "") == "en_progreso"),
        "completados": sum(1 for m in mantenimientos if (m.get("estado") or "") in ("completado", "finalizado")),
    }

    conn.close()
    return render_template("mantenimientos.html", mantenimientos=mantenimientos, stats=stats, resolver=_fetch_equipo_display)


@mantenimientos_bp.route("/nuevo", methods=["POST"])
def crear_mantenimiento():
    data = request.form
    equipo_id = data.get("equipo_id")
    tipo_equipo = data.get("tipo_equipo", "individual")
    titulo = data.get("titulo")
    descripcion = data.get("descripcion")
    responsable = data.get("responsable")
    fecha_programada = data.get("fecha_programada")
    estado = data.get("estado", "pendiente")
    costo = data.get("costo") or None

    if not equipo_id or not titulo:
        flash("Equipo y título son obligatorios", "danger")
        return redirect(url_for("mantenimientos.dashboard"))

    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute(
            """
            INSERT INTO mantenimientos (
                equipo_id, tipo_equipo, titulo, descripcion, responsable,
                fecha_programada, estado, costo, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                equipo_id,
                tipo_equipo,
                titulo,
                descripcion,
                responsable,
                fecha_programada,
                estado,
                costo,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        flash("Mantenimiento registrado", "success")
    except Exception as exc:
        conn.rollback()
        flash(f"Error al guardar: {exc}", "danger")
    finally:
        conn.close()
    return redirect(url_for("mantenimientos.dashboard"))


@mantenimientos_bp.route("/api/list", methods=["GET"])
def api_list():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM mantenimientos ORDER BY datetime(created_at) DESC")
    data = [dict(row) for row in c.fetchall()]
    conn.close()
    return jsonify(data)
