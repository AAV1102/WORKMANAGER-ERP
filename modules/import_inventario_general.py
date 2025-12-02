from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os

inventario_import_bp = Blueprint('inventario_import', __name__, template_folder='../templates', static_folder='../static')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workmanager_erp.db")

@inventario_import_bp.route('/inventario_import/form_inventario_general', methods=['GET', 'POST'])
def form_inventario_general():
    flash('Ahora usamos el Importador Universal centralizado.', 'info')
    return redirect(url_for('export_import_v2.importar_form'))
