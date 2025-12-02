from flask import Blueprint, render_template, jsonify
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workmanager_erp.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

infraestructura_bp = Blueprint('infraestructura', __name__)

@infraestructura_bp.route('/infraestructura')
def infraestructura():
    conn = get_conn()
    c = conn.cursor()
    # Stats from equipos_individuales
    servidores = c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE tecnologia LIKE '%Servidor%'").fetchone()[0]
    redes = c.execute("""
        SELECT COUNT(*) FROM equipos_individuales
        WHERE tecnologia IN ('Switch','Switches','Router','Routers','Firewall','Firewall Sophos','Access Point','Mikrotik','Microtik','Cisco')
    """).fetchone()[0]
    almacenamiento = c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE tipo_disco IS NOT NULL OR espacio_disco IS NOT NULL").fetchone()[0]
    virtual = c.execute("SELECT COUNT(*) FROM equipos_agrupados WHERE descripcion_general LIKE '%VM%' OR descripcion_general LIKE '%Virtual%'").fetchone()[0]
    sedes = c.execute("SELECT COUNT(*) FROM sedes").fetchone()[0]
    conn.close()
    stats = {
        "servidores": servidores,
        "redes": redes,
        "almacenamiento": almacenamiento,
        "virtualizacion": virtual,
        "sedes": sedes,
    }
    return render_template('infraestructura.html', stats=stats, section=None)

@infraestructura_bp.route('/infraestructura/servidores')
def servidores():
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, codigo_barras_individual, placa, marca, modelo, so, estado, sede_id
        FROM equipos_individuales
        WHERE tecnologia LIKE '%Servidor%'
        ORDER BY updated_at DESC
    """).fetchall()
    conn.close()
    return render_template('infraestructura.html', section='servidores', data=rows)

@infraestructura_bp.route('/infraestructura/redes')
def redes():
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, codigo_barras_individual, marca, modelo, tecnologia, estado, sede_id
        FROM equipos_individuales
        WHERE tecnologia IN ('Switch','Switches','Router','Routers','Firewall','Firewall Sophos','Access Point','Mikrotik','Microtik','Cisco')
        ORDER BY updated_at DESC
    """).fetchall()
    conn.close()
    return render_template('infraestructura.html', section='redes', data=rows)

@infraestructura_bp.route('/infraestructura/almacenamiento')
def almacenamiento():
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, codigo_barras_individual, marca, modelo, tipo_disco, espacio_disco, estado, sede_id
        FROM equipos_individuales
        WHERE tipo_disco IS NOT NULL OR espacio_disco IS NOT NULL
        ORDER BY updated_at DESC
    """).fetchall()
    conn.close()
    return render_template('infraestructura.html', section='almacenamiento', data=rows)

@infraestructura_bp.route('/infraestructura/virtualizacion')
def virtualizacion():
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, codigo_barras_unificado, descripcion_general, estado_general, sede_id
        FROM equipos_agrupados
        WHERE descripcion_general LIKE '%Virtual%' OR descripcion_general LIKE '%VM%'
        ORDER BY updated_at DESC
    """).fetchall()
    conn.close()
    return render_template('infraestructura.html', section='virtualizacion', data=rows)

@infraestructura_bp.route('/infraestructura/api/resumen')
def api_resumen_infraestructura():
    conn = get_conn()
    c = conn.cursor()
    data = {
        "servidores": c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE tecnologia LIKE '%Servidor%'").fetchone()[0],
        "redes": c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE tecnologia IN ('Switch','Switches','Router','Routers','Firewall','Firewall Sophos','Access Point','Mikrotik','Microtik','Cisco')").fetchone()[0],
        "almacenamiento": c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE tipo_disco IS NOT NULL OR espacio_disco IS NOT NULL").fetchone()[0],
        "virtualizacion": c.execute("SELECT COUNT(*) FROM equipos_agrupados WHERE descripcion_general LIKE '%Virtual%' OR descripcion_general LIKE '%VM%'").fetchone()[0],
        "sedes": c.execute("SELECT COUNT(*) FROM sedes").fetchone()[0],
    }
    conn.close()
    return jsonify(data)
