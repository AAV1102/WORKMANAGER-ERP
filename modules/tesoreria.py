from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
import sqlite3
from functools import wraps

tesoreria_bp = Blueprint('tesoreria', __name__, url_prefix='/tesoreria', template_folder='../templates')

def get_conn():
    conn = sqlite3.connect('workmanager_erp.db')
    conn.row_factory = sqlite3.Row
    return conn

@tesoreria_bp.route('/')
@login_required
def index():
    """Sirve la página principal del dashboard de Tesorería."""
    return render_template('tesoreria.html')

@tesoreria_bp.route('/api/dashboard')
@login_required
def get_dashboard_data():
    """API que provee todos los datos para el dashboard de Tesorería."""
    conn = get_conn()
    try:
        total_facturas = conn.execute("SELECT COUNT(id) FROM facturas_proveedores").fetchone()[0] or 0
        monto_pendiente = conn.execute("SELECT IFNULL(SUM(monto), 0) FROM facturas_proveedores WHERE estado = 'pendiente'").fetchone()[0] or 0
        monto_pagado = conn.execute("SELECT IFNULL(SUM(monto), 0) FROM facturas_proveedores WHERE estado = 'pagada'").fetchone()[0] or 0
        
        facturas_recientes = conn.execute("""
            SELECT fp.id, fp.numero_factura, fp.monto, fp.fecha_emision, fp.estado, p.nombre as nombre_proveedor
            FROM facturas_proveedores fp
            LEFT JOIN proveedores p ON fp.proveedor_id = p.id
            ORDER BY fp.fecha_emision DESC LIMIT 10
        """).fetchall()

        return jsonify({
            "stats": {
                "total_facturas": total_facturas,
                "monto_pendiente": monto_pendiente,
                "monto_pagado": monto_pagado
            },
            "facturas_recientes": [dict(f) for f in facturas_recientes]
        })
    finally:
        conn.close()

def permission_required(perm):
    def decorator(f):
        @login_required
        @wraps(f)
        def wrapper(*args, **kwargs):
            from app import user_has_permission
            if not current_user or not user_has_permission(current_user.id, perm):
                flash('No tienes permisos para esta acción.')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return wrapper
    return decorator
