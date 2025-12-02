# flask-todo-app/inventory/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
import os
import shutil
from werkzeug.utils import secure_filename
from datetime import datetime
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

from .processor import process_inventory_files
from models import db, InventoryItem # Asumimos que models.py está en la raíz

# Crear el Blueprint
inventory_bp = Blueprint('inventory', __name__,
                         template_folder='../templates/inventory', # Apunta a la carpeta de templates correcta
                         static_folder='../static')

@inventory_bp.route('/')
def index():
    """Página principal del módulo de inventario."""
    return render_template('upload.html')

@inventory_bp.route('/upload', methods=['POST'])
def upload_and_process():
    """Maneja la subida de archivos, los procesa y los guarda en la base de datos."""
    files = request.files.getlist('inventory_files')
    if not files or all(f.filename == '' for f in files):
        flash('No se seleccionaron archivos válidos.', 'error')
        return redirect(url_for('inventory.index'))

    temp_upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(datetime.now().timestamp()).replace('.', ''))
    os.makedirs(temp_upload_path, exist_ok=True)

    for file in files:
        filename = secure_filename(file.filename)
        file.save(os.path.join(temp_upload_path, filename))

    df_processed, error = process_inventory_files(temp_upload_path)
    shutil.rmtree(temp_upload_path)

    if error:
        flash(f"Error al procesar los archivos: {error}", 'error')
        return redirect(url_for('inventory.index'))
    
    if df_processed is None or df_processed.empty:
        flash("No se generaron datos de inventario válidos.", 'warning')
        return redirect(url_for('inventory.index'))

    try:
        db.session.query(InventoryItem).delete()
        db.session.commit()

        # Convertir el DataFrame a una lista de diccionarios y guardar en la DB
        # Asegura que solo se inserten columnas que existen en el modelo
        model_columns = {c.name for c in InventoryItem.__table__.columns}
        df_columns = set(df_processed.columns)
        valid_columns = list(model_columns.intersection(df_columns))
        
        df_db_ready = df_processed[valid_columns]
        df_db_ready.to_sql('inventory_items', db.engine, if_exists='append', index=False)
        
        flash(f"¡Éxito! Se guardaron {len(df_processed)} ítems en la base de datos.", 'success')
        return redirect(url_for('inventory.view'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error crítico al guardar en la base de datos: {e}", 'error')
        return redirect(url_for('inventory.index'))

@inventory_bp.route('/view')
def view():
    """Muestra el inventario actual desde la base de datos."""
    items = InventoryItem.query.all()
    return render_template('view.html', items=items)

@inventory_bp.route('/download')
def download_excel():
    """Genera y permite descargar el inventario actual de la base de datos como un archivo Excel."""
    items = InventoryItem.query.all()
    if not items:
        flash("No hay datos en el inventario para exportar.", 'warning')
        return redirect(url_for('inventory.view'))

    data = [item.__dict__ for item in items]
    df_db = pd.DataFrame(data)
    df_db.drop('_sa_instance_state', axis=1, inplace=True, errors='ignore')

    wb = Workbook()
    ws = wb.active
    ws.title = "INVENTARIO_GENERAL"
    
    for r in dataframe_to_rows(df_db, index=False, header=True):
        ws.append(r)

    reports_dir = os.path.join(current_app.static_folder, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    filename = f"INVENTARIO_EXPORTADO_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(reports_dir, filename)
    wb.save(filepath)

    return send_from_directory(reports_dir, filename, as_attachment=True)
