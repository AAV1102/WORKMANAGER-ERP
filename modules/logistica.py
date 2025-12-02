from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
import sqlite3

logistica_bp = Blueprint('logistica', __name__)

# Assuming compras_articulos table exists, but since not in init_db, we'll create it or virtual
# For now, virtual data

@logistica_bp.route('/logistica')
@login_required
def index():
    # Virtual data - in real, from DB
    total_ordenes = 0
    total_proveedores = 80  # Mock data
    ordenes = [
        {'id': 1, 'numero_orden': 'ORD001', 'entidad': 'Proveedor A', 'estado': 'Pendiente'},
        {'id': 2, 'numero_orden': 'ORD002', 'entidad': 'Proveedor B', 'estado': 'Aprobada'}
    ]
    return render_template('logistica.html', total_ordenes=total_ordenes, total_proveedores=total_proveedores, ordenes=ordenes[:5])

@logistica_bp.route('/logistica/ordenes/add', methods=['GET', 'POST'])
@login_required
def add_orden():
    if request.method == 'POST':
        servicio = request.form.get('servicio')
        solicitante = request.form.get('solicitante')
        entidad = request.form.get('entidad')
        flash("Orden de compra agregada", 'success')
        return redirect(url_for('logistica.index'))
    return render_template('logistica_add_orden.html')

@logistica_bp.route('/logistica/proveedores', methods=['GET'])
@login_required
def proveedores():
    proveedores = ['Proveedor A', 'Proveedor B']  # Mock
    return render_template('logistica_proveedores.html', proveedores=proveedores)

@logistica_bp.route('/api/logistica/ordenes', methods=['GET'])
def api_ordenes():
    search = request.args.get('search', '')
    ordenes = [
        {'id': 1, 'numero_orden': 'ORD001', 'entidad': 'Proveedor A', 'estado': 'Pendiente'},
        {'id': 2, 'numero_orden': 'ORD002', 'entidad': 'Proveedor B', 'estado': 'Aprobada'}
    ]
    if search:
        ordenes = [o for o in ordenes if search.lower() in o['numero_orden'].lower() or search.lower() in o['entidad'].lower()]
    return jsonify(ordenes)

# RBAC placeholder
from functools import wraps
def permission_required(perm):
    def decorator(f):
        @login_required
        @wraps(f)
        def wrapper(*args, **kwargs):
            from app import user_has_permission
            from flask import current_user
            if not current_user or not user_has_permission(current_user.id, perm):
                flash('No tienes permisos para esta acción.')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return wrapper
    return decorator
