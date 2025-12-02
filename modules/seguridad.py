from flask import Blueprint, render_template, jsonify
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workmanager_erp.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

seguridad_bp = Blueprint('seguridad', __name__)

@seguridad_bp.route('/seguridad')
def seguridad():
    conn = get_conn()
    c = conn.cursor()
    total_equipos = c.execute("SELECT COUNT(*) FROM equipos_individuales").fetchone()[0]
    asignados = c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE estado = 'asignado'").fetchone()[0]
    disponibles = c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE estado = 'disponible'").fetchone()[0]
    alertas = c.execute("SELECT * FROM ai_logs ORDER BY created_at DESC LIMIT 5").fetchall()
    conn.close()
    stats = {
        "proteccion": 95 if total_equipos else 0,
        "firewall": 100,
        "alertas": len(alertas),
        "cumplimiento": 98,
        "total_equipos": total_equipos,
        "asignados": asignados,
        "disponibles": disponibles,
    }
    return render_template('seguridad.html', stats=stats, alertas=alertas)

@seguridad_bp.route('/seguridad/antivirus')
def antivirus():
    conn = get_conn()
    rows = conn.execute("SELECT id, codigo_barras_individual, marca, modelo, so, estado FROM equipos_individuales ORDER BY updated_at DESC LIMIT 50").fetchall()
    conn.close()
    return render_template('seguridad.html', section='antivirus', data=rows)

@seguridad_bp.route('/seguridad/firewall')
def firewall():
    conn = get_conn()
    rows = conn.execute("SELECT id, tecnologia, marca, modelo, estado FROM equipos_individuales WHERE tecnologia IN ('Firewall','Firewall Sophos') ORDER BY updated_at DESC").fetchall()
    conn.close()
    return render_template('seguridad.html', section='firewall', data=rows)

@seguridad_bp.route('/seguridad/auditoria')
def auditoria():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM ai_logs ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return render_template('seguridad.html', section='auditoria', data=rows)

@seguridad_bp.route('/seguridad/politicas')
def politicas():
    conn = get_conn()
    rows = conn.execute("SELECT nombre, ciudad, responsable FROM sedes").fetchall()
    conn.close()
    return render_template('seguridad.html', section='politicas', data=rows)

@seguridad_bp.route('/seguridad/api/resumen')
def api_resumen_seguridad():
    conn = get_conn()
    c = conn.cursor()
    data = {
        "total_equipos": c.execute("SELECT COUNT(*) FROM equipos_individuales").fetchone()[0],
        "asignados": c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE estado='asignado'").fetchone()[0],
        "disponibles": c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE estado='disponible'").fetchone()[0],
        "alertas": c.execute("SELECT COUNT(*) FROM ai_logs").fetchone()[0],
    }
    conn.close()
    return jsonify(data)
