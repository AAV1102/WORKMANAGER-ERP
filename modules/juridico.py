from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required
import sqlite3
import logging

logger = logging.getLogger(__name__)

juridico_bp = Blueprint('juridico', __name__)

# Since there are no casos, contratos tables, we'll create virtual data for now and add to DB later if needed
# For complete implementation, we'd create tables for contratos, casos, audiencias, etc.

@juridico_bp.route('/juridico')
@login_required
def index():
    # Virtual data - in production, this would come from DB
    casos = [
        {'id': 1, 'numero_caso': 'CASO001', 'tipo': 'Laboral', 'estado': 'En proceso', 'tipo': 'Laboral'},
        {'id': 2, 'numero_caso': 'CASO002', 'tipo': 'Contrato', 'estado': 'Resuelto', 'tipo': 'Contrato'}
    ]
    contratos = [
        {'id': 1, 'numero_contrato': 'CON001', 'tipo': 'Servicio', 'estado': 'Activo'},
        {'id': 2, 'numero_contrato': 'CON002', 'tipo': 'Compra', 'estado': 'En revisión'}
    ]
    audiencias = [
        {'id': 1, 'fecha': '2024-01-15', 'tipo': 'Audiencia', 'estado': 'Programada'},
        {'id': 2, 'fecha': '2024-01-20', 'tipo': 'Contestación', 'estado': 'Pendiente'}
    ]

    return render_template('juridico.html', casos=len(casos), contratos=len(contratos), audiencias=len(audiencias), casos_list=casos[:5], contratos_list=contratos[:5], audiencias_list=audiencias[:5])

@juridico_bp.route('/juridico/casos/add', methods=['GET', 'POST'])
@login_required
def add_caso():
    if request.method == 'POST':
        # In production, save to DB
        numero = request.form.get('numero_caso')
        tipo = request.form.get('tipo')
        descripcion = request.form.get('descripcion')
        estado = request.form.get('estado', 'En proceso')
        flash('Caso agregado', 'success')
        return redirect(url_for('juridico.index'))
    return render_template('juridico_add_caso.html')

@juridico_bp.route('/juridico/contratos/add', methods=['GET', 'POST'])
@login_required
def add_contrato():
    if request.method == 'POST':
        numero = request.form.get('numero_contrato')
        tipo = request.form.get('tipo')
        fecha_inicio = request.form.get('fecha_inicio')
        fecha_fin = request.form.get('fecha_fin')
        partes = request.form.get('partes')
        flash('Contrato agregado', 'success')
        return redirect(url_for('juridico.index'))
    return render_template('juridico_add_contrato.html')

@juridico_bp.route('/api/juridico/casos', methods=['GET'])
def api_casos():
    # Mock API endpoint
    casos = [
        {'id': 1, 'numero_caso': 'CASO001', 'tipo': 'Laboral', 'estado': 'En proceso'},
        {'id': 2, 'numero_caso': 'CASO002', 'tipo': 'Contrato', 'estado': 'Resuelto'}
    ]
    search = request.args.get('search', '')
    if search:
        casos = [c for c in casos if search.lower() in c.get('numero_caso', '').lower() or search.lower() in c.get('tipo', '').lower()]
    return jsonify(casos)

@juridico_bp.route('/juridico/edit/<tipo>/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(tipo, id):
    # Generic edit route for casos, contratos
    if tipo == 'caso':
        if request.method == 'POST':
            flash('Caso editado', 'success')
            return redirect(url_for('juridico.index'))
        return render_template('juridico_edit_caso.html', item_id=id)
    elif tipo == 'contrato':
        if request.method == 'POST':
            flash('Contrato editado', 'success')
            return redirect(url_for('juridico.index'))
        return render_template('juridico_edit_contrato.html', item_id=id)
    else:
        flash('Tipo no válido', 'error')
        return redirect(url_for('juridico.index'))

@juridico_bp.route('/juridico/delete/<tipo>/<int:id>', methods=['POST'])
@login_required
def delete(tipo, id):
    # Generic delete
    flash(f'{tipo.title()} eliminado', 'success')
    return redirect(url_for('juridico.index'))

# RBAC decorator
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

