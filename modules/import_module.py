from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
import os
import pandas as pd
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime

import_bp = Blueprint('import_module', __name__, template_folder='../templates', static_folder='../static')

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    db_path = os.path.join(current_app.root_path, 'workmanager_erp.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def get_column_mapping(table_name):
    """Retorna el mapeo de columnas según la tabla destino."""
    if table_name == 'equipos_individuales':
        return {
            # Columnas comunes del Excel
            'Código Activo': 'codigo_barras_individual',
            'Serial': 'serial',
            'Marca': 'marca',
            'Modelo': 'modelo',
            'Procesador': 'procesador',
            'RAM': 'cantidad_ram',
            'Disco Duro': 'espacio_disco',
            'Sistema Operativo': 'so',
            'Estado': 'estado',
            'Usuario Asignado': 'asignado_nuevo',
            'Fecha Compra': 'fecha',
            'Proveedor': 'proveedor',
            'Observaciones': 'observaciones',
            'Sede': 'sede_id',
            'Creador': 'creador_registro',

            # Variaciones posibles
            'Código de Barras': 'codigo_barras_individual',
            'Número Serial': 'serial',
            'Tipo de Disco': 'tipo_disco',
            'Espacio en Disco': 'espacio_disco',
            'SO': 'so',
            'Fecha de Compra': 'fecha',
            'Usuario': 'asignado_nuevo',
            'Creado por': 'creador_registro'
        }
    elif table_name == 'equipos_agrupados':
        return {
            'Código Barras Unificado': 'codigo_barras_unificado',
            'Descripción': 'descripcion_general',
            'Asignado Actual': 'asignado_actual',
            'Sede': 'sede_id',
            'Estado': 'estado_general',
            'Creador': 'creador_registro',
            'Observaciones': 'observaciones'
        }
    elif table_name == 'usuarios':
        return {
            'Cédula': 'cedula',
            'Nombre': 'nombre',
            'Apellido': 'apellido',
            'Email': 'email',
            'Cargo': 'cargo',
            'Departamento': 'departamento',
            'Teléfono': 'telefono',
            'Estado': 'estado'
        }
    elif table_name == 'empleados':
        return {
            'Cédula': 'cedula',
            'Nombre': 'nombre',
            'Apellido': 'apellido',
            'Email': 'email',
            'Cargo': 'cargo',
            'Departamento': 'departamento',
            'Teléfono': 'telefono',
            'Estado': 'estado',
            'Fecha Ingreso': 'fecha_ingreso',
            'Salario': 'salario'
        }
    else:
        return {}

def get_table_columns(cursor, table_name):
    """Obtiene los nombres de las columnas de una tabla."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    return [col[1] for col in columns_info]

def import_excel_to_db(excel_file_path, table_name='equipos_individuales'):
    """
    Importa datos desde un archivo Excel a la tabla especificada de la base de datos.
    """
    try:
        # Leer el archivo Excel
        df = pd.read_excel(excel_file_path)

        # Conectar a la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        # Mapeo de columnas del Excel a la base de datos
        column_mapping = get_column_mapping(table_name)

        # Renombrar columnas según el mapeo
        df.rename(columns=column_mapping, inplace=True)

        # Filtrar solo las columnas que existen en la tabla
        table_columns = get_table_columns(cursor, table_name)
        df = df[[col for col in df.columns if col in table_columns]]

        # Convertir DataFrame a lista de tuplas para inserción
        records = df.to_records(index=False)
        data_tuples = [tuple(record) for record in records]

        # Preparar la consulta de inserción
        placeholders = ', '.join(['?' for _ in df.columns])
        columns_str = ', '.join(df.columns)
        insert_query = f"INSERT OR IGNORE INTO {table_name} ({columns_str}) VALUES ({placeholders})"

        # Insertar los datos
        inserted_count = 0
        errors = []

        for i, data_tuple in enumerate(data_tuples):
            try:
                cursor.execute(insert_query, data_tuple)
                inserted_count += 1
            except Exception as row_error:
                errors.append(f"Fila {i+2}: {str(row_error)}")
                continue

        # Confirmar cambios
        conn.commit()
        conn.close()

        return {
            'success': True,
            'inserted': inserted_count,
            'total': len(data_tuples),
            'duplicates': len(data_tuples) - inserted_count,
            'errors': errors,
            'columns_mapped': list(df.columns)
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@import_bp.route('/import')
def import_dashboard():
    """Dashboard principal de importación"""
    return render_template('import_dashboard.html')

@import_bp.route('/import/upload', methods=['POST'])
def upload_file():
    """Maneja la subida y procesamiento de archivos Excel"""
    if 'file' not in request.files:
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('import_module.import_dashboard'))

    file = request.files['file']
    table_name = request.form.get('table_name', 'equipos_individuales')

    if file.filename == '':
        flash('No se seleccionó ningún archivo', 'error')
        return redirect(url_for('import_module.import_dashboard'))

    if not allowed_file(file.filename):
        flash('Tipo de archivo no permitido. Solo se permiten .xlsx, .xls y .csv', 'error')
        return redirect(url_for('import_module.import_dashboard'))

    # Crear directorio de uploads si no existe
    upload_folder = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)

    # Guardar archivo temporalmente
    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_folder, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}")
    file.save(file_path)

    try:
        # Procesar el archivo
        result = import_excel_to_db(file_path, table_name)

        # Limpiar archivo temporal
        os.remove(file_path)

        if result['success']:
            flash(f"✅ Importación exitosa! Se insertaron {result['inserted']} registros en {table_name}", 'success')

            # Guardar detalles en sesión para mostrar en resultados
            import_details = {
                'table': table_name,
                'inserted': result['inserted'],
                'total': result['total'],
                'duplicates': result['duplicates'],
                'columns': result['columns_mapped'],
                'errors': result['errors'][:10]  # Mostrar máximo 10 errores
            }

            # Aquí podrías guardar los detalles en la base de datos para un log de importaciones
            log_import(import_details)

        else:
            flash(f"❌ Error en la importación: {result['error']}", 'error')

    except Exception as e:
        # Limpiar archivo temporal en caso de error
        if os.path.exists(file_path):
            os.remove(file_path)
        flash(f"❌ Error procesando el archivo: {str(e)}", 'error')

    return redirect(url_for('import_module.import_dashboard'))

@import_bp.route('/import/preview', methods=['POST'])
def preview_import():
    """Vista previa del archivo Excel antes de importar"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    table_name = request.form.get('table_name', 'equipos_individuales')

    if not allowed_file(file.filename):
        return jsonify({'error': 'Tipo de archivo no permitido'}), 400

    try:
        # Leer las primeras filas del archivo
        df = pd.read_excel(file)

        # Obtener mapeo de columnas
        column_mapping = get_column_mapping(table_name)

        # Crear preview data
        preview_data = {
            'columns': list(df.columns),
            'mapped_columns': [column_mapping.get(col, col) for col in df.columns],
            'rows': df.head(5).to_dict('records'),  # Primeras 5 filas
            'total_rows': len(df)
        }

        return jsonify(preview_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@import_bp.route('/import/tables')
def get_available_tables():
    """Obtiene la lista de tablas disponibles para importación"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tablas principales para importación
    available_tables = [
        {'name': 'equipos_individuales', 'label': 'Equipos Individuales', 'description': 'Computadores, laptops, equipos individuales'},
        {'name': 'equipos_agrupados', 'label': 'Equipos Agrupados', 'description': 'Equipos agrupados por tandas'},
        {'name': 'usuarios', 'label': 'Usuarios', 'description': 'Usuarios del sistema'},
        {'name': 'empleados', 'label': 'Empleados', 'description': 'Información de empleados'},
        {'name': 'licencias_office365', 'label': 'Licencias Office 365', 'description': 'Licencias de Microsoft Office'},
        {'name': 'pacientes', 'label': 'Pacientes', 'description': 'Registros médicos'},
        {'name': 'medicos', 'label': 'Médicos', 'description': 'Información de médicos'},
        {'name': 'sedes', 'label': 'Sedes', 'description': 'Información de sedes'}
    ]

    conn.close()
    return jsonify(available_tables)

def log_import(import_details):
    """Registra la importación en un log (puedes implementar esto en una tabla dedicada)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Aquí podrías crear una tabla import_logs si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS import_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                records_inserted INTEGER,
                records_total INTEGER,
                records_duplicates INTEGER,
                columns_mapped TEXT,
                errors TEXT,
                imported_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            INSERT INTO import_logs (table_name, records_inserted, records_total, records_duplicates, columns_mapped, errors)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            import_details['table'],
            import_details['inserted'],
            import_details['total'],
            import_details['duplicates'],
            ','.join(import_details['columns']),
            '\n'.join(import_details['errors'])
        ))

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Error logging import: {e}")
        # No fallar la importación por error en el log
