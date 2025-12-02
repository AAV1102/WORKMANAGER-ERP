from flask import Blueprint, jsonify
from flask_login import login_required
import sqlite3

dashboard_manager_bp = Blueprint('dashboard_manager', __name__, url_prefix='/dashboard')

def get_db_connection():
    conn = sqlite3.connect('workmanager_erp.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Definición de Widgets Disponibles ---
# Cada función obtiene los datos para un widget específico.

def get_kpi_empleados():
    conn = get_db_connection()
    activos = conn.execute("SELECT COUNT(id) FROM empleados WHERE estado = 'activo'").fetchone()[0]
    total = conn.execute("SELECT COUNT(id) FROM empleados").fetchone()[0]
    conn.close()
    return {'title': 'Empleados Activos', 'value': activos, 'total': total, 'icon': 'fa-users'}

def get_kpi_inventario():
    conn = get_db_connection()
    asignados = conn.execute("SELECT COUNT(id) FROM equipos_individuales WHERE estado = 'asignado'").fetchone()[0]
    total = conn.execute("SELECT COUNT(id) FROM equipos_individuales").fetchone()[0]
    conn.close()
    return {'title': 'Equipos Asignados', 'value': asignados, 'total': total, 'icon': 'fa-laptop'}

def get_kpi_licencias():
    conn = get_db_connection()
    try:
        asignadas, total = conn.execute("SELECT SUM(licencias_asignadas), SUM(total_licencias) FROM licencias_m365_resumen").fetchone()
    except (sqlite3.OperationalError, TypeError):
        asignadas, total = 0, 0
    conn.close()
    return {'title': 'Licencias Asignadas', 'value': asignadas or 0, 'total': total or 0, 'icon': 'fa-key'}

def get_kpi_tickets():
    conn = get_db_connection()
    try:
        abiertos = conn.execute("SELECT COUNT(id) FROM tickets WHERE estado = 'abierto'").fetchone()[0]
        total = conn.execute("SELECT COUNT(id) FROM tickets").fetchone()[0]
    except (sqlite3.OperationalError, TypeError):
        abiertos, total = 0, 0
    conn.close()
    return {'title': 'Tickets Abiertos', 'value': abiertos, 'total': total, 'icon': 'fa-headset'}

def get_kpi_inventario_por_estado():
    """Nuevo widget que cuenta equipos por cada estado."""
    conn = get_db_connection()
    try:
        # Agrupa por estado y cuenta cuántos hay en cada grupo
        estados = conn.execute("""
            SELECT estado, COUNT(id) as cantidad
            FROM equipos_individuales
            GROUP BY estado
            ORDER BY cantidad DESC
        """).fetchall()
    except sqlite3.OperationalError:
        estados = []
    conn.close()
    # Devuelve un tipo 'list' para que el frontend sepa cómo renderizarlo
    return {'title': 'Equipos por Estado', 'type': 'list', 'icon': 'fa-clipboard-check', 'data': [dict(e) for e in estados]}

WIDGETS = {
    'empleados': get_kpi_empleados,
    'inventario': get_kpi_inventario,
    'licencias': get_kpi_licencias,
    'tickets': get_kpi_tickets,
    'inventario_estado': get_kpi_inventario_por_estado, # Registrar el nuevo widget
}

@dashboard_manager_bp.route('/widget_data/<widget_name>')
@login_required
def get_widget_data(widget_name):
    if widget_name in WIDGETS:
        return jsonify(WIDGETS[widget_name]())
    return jsonify({'error': 'Widget no encontrado'}), 404