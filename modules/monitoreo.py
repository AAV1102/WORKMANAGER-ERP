from flask import Blueprint, render_template, jsonify
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workmanager_erp.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

monitoreo_bp = Blueprint('monitoreo', __name__)

@monitoreo_bp.route('/monitoreo')
def monitoreo():
    conn = get_conn()
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM equipos_individuales").fetchone()[0]
    activos = c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE estado = 'asignado'").fetchone()[0]
    disponibles = c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE estado = 'disponible'").fetchone()[0]
    bajas = c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE estado = 'baja'").fetchone()[0]
    conn.close()
    stats = {
        "uptime": 98 if total else 0,
        "activos": activos,
        "disponibles": disponibles,
        "bajas": bajas,
        "total": total,
    }
    return render_template('monitoreo.html', stats=stats)

@monitoreo_bp.route('/monitoreo/sistema')
def sistema():
    conn = get_conn()
    rows = conn.execute("SELECT id, codigo_barras_individual, marca, modelo, so, estado FROM equipos_individuales ORDER BY updated_at DESC LIMIT 50").fetchall()
    conn.close()
    return render_template('monitoreo.html', section='sistema', data=rows)

@monitoreo_bp.route('/monitoreo/red')
def red():
    conn = get_conn()
    rows = conn.execute("SELECT id, codigo_barras_individual, marca, modelo, tecnologia, estado FROM equipos_individuales WHERE tecnologia IN ('Switch','Switches','Router','Routers','Access Point','Firewall','Firewall Sophos') ORDER BY updated_at DESC").fetchall()
    conn.close()
    return render_template('monitoreo.html', section='red', data=rows)

@monitoreo_bp.route('/monitoreo/aplicaciones')
def aplicaciones():
    conn = get_conn()
    # Apalancamos licencias como proxy de apps monitoreadas
    rows = conn.execute("SELECT id, email, tipo_licencia, estado, updated_at FROM licencias_office365 ORDER BY updated_at DESC LIMIT 50").fetchall()
    conn.close()
    return render_template('monitoreo.html', section='aplicaciones', data=rows)

@monitoreo_bp.route('/monitoreo/seguridad')
def seguridad():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM ai_logs ORDER BY created_at DESC LIMIT 20").fetchall()
    conn.close()
    return render_template('monitoreo.html', section='seguridad', data=rows)

@monitoreo_bp.route('/monitoreo/api/resumen')
def api_resumen_monitoreo():
    conn = get_conn()
    c = conn.cursor()
    data = {
        "total": c.execute("SELECT COUNT(*) FROM equipos_individuales").fetchone()[0],
        "asignados": c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE estado='asignado'").fetchone()[0],
        "disponibles": c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE estado='disponible'").fetchone()[0],
        "baja": c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE estado='baja'").fetchone()[0],
    }
    conn.close()
    return jsonify(data)
