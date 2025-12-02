import os
import sqlite3
import pandas as pd
import time
from flask import (
    Blueprint,
    request,
    jsonify,
    send_file,
    current_app,
    Response,
    render_template,
    flash,
    redirect,
    url_for,
)
from openpyxl import Workbook
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
try:
    from barcode import Code128
    from barcode.writer import ImageWriter
    BARCODE_AVAILABLE = True
except Exception:
    BARCODE_AVAILABLE = False
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import csv
import json
import re
from datetime import datetime
import os
import json as pyjson

from modules.export_import import (
    TMP_DIR,
    load_dataframes,
    build_column_mapping,
    detect_target_from_headers,
    import_rows,
)
from werkzeug.utils import secure_filename

# Nombre unico para evitar choque con el blueprint legacy de importador
export_import_bp = Blueprint('export_import_v2', __name__)

# Alias amigables desde UI -> tablas reales
TABLE_ALIASES = {
    "agrupados": "equipos_agrupados",
    "individuales": "equipos_individuales",
    "asignados": "equipos_individuales",
    "bajas": "inventario_bajas",
    "licencias": "licencias_office365",
    "empleados": "empleados",
    "inventarios": "equipos_individuales",
    "importador": "equipos_individuales",
}

MODULES = [
    {"alias": "equipos_individuales", "label": "Inventario Tecnológico", "description": "Base maestra de equipos individuales (PC, servidores, laptops, monitoreo)."},
    {"alias": "licencias_office365", "label": "Licencias Microsoft 365", "description": "Control de licencias activas/asignadas por sede y usuario."},
    {"alias": "empleados", "label": "Empleados / RRHH", "description": "Datos personales, contratos y códigos biométricos sincronizados con inventario."},
    {"alias": "inventario_bajas", "label": "Equipos Dados de Baja", "description": "Histórico de descartes y equipos reciclados."},
]
EXPORT_FORMATS = ["excel", "csv", "json", "pdf", "txt", "image"]

def get_db_connection():
    conn = sqlite3.connect('workmanager_erp.db')
    conn.row_factory = sqlite3.Row
    return conn

@export_import_bp.route('/export/excel/<table>')
def export_excel(table):
    try:
        table_real = resolve_table(table)
        if not table_exists(table_real):
            return jsonify({'error': f'No existe la tabla {table_real}'}), 404
        # Get selected columns from request
        selected_columns = request.args.get('columns', '').split(',') if request.args.get('columns') else None

        conn = get_db_connection()
        query = f"SELECT * FROM {table_real}"
        df = pd.read_sql_query(query, conn)
        conn.close()

        # Filter columns if specified
        if selected_columns and selected_columns[0]:
            available_columns = [col for col in selected_columns if col in df.columns]
            if available_columns:
                df = df[available_columns]

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=table, index=False)

        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=safe_filename(table_real, 'xlsx')
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_import_bp.route('/export/json/<table>')
def export_json(table):
    try:
        table_real = resolve_table(table)
        if not table_exists(table_real):
            return jsonify({'error': f'No existe la tabla {table_real}'}), 404
        conn = get_db_connection()
        query = f"SELECT * FROM {table_real}"
        df = pd.read_sql_query(query, conn)
        conn.close()

        # Convert DataFrame to JSON
        json_data = df.to_json(orient='records', date_format='iso', indent=2)

        # Create response
        response = Response(
            json_data,
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename={safe_filename(table_real, "json")}'}
        )
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_import_bp.route('/export/pdf/<table>')
def export_pdf(table):
    try:
        table_real = resolve_table(table)
        if not table_exists(table_real):
            return jsonify({'error': f'No existe la tabla {table_real}'}), 404
        # Get selected columns from request
        selected_columns = request.args.get('columns', '').split(',') if request.args.get('columns') else None

        conn = get_db_connection()
        query = f"SELECT * FROM {table_real}"
        if selected_columns and selected_columns[0]:
            query = f"SELECT {', '.join(selected_columns)} FROM {table_real}"

        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        conn.close()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Title
        styles = getSampleStyleSheet()
        title = Paragraph(f"Reporte de {table.title()}", styles['Title'])
        elements.append(title)

        # Table data
        data = [column_names] + [list(row) for row in rows]

        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#343a40'),
            ('TEXTCOLOR', (0, 0), (-1, 0), '#ffffff'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), '#f8f9fa'),
            ('TEXTCOLOR', (0, 1), (-1, -1), '#000000'),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, '#000000'),
        ]))

        elements.append(table)
        doc.build(elements)

        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=safe_filename(table_real, 'pdf')
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_import_bp.route('/export/csv/<table>')
def export_csv(table):
    try:
        table_real = resolve_table(table)
        if not table_exists(table_real):
            return jsonify({'error': f'No existe la tabla {table_real}'}), 404
        # Get selected columns from request
        selected_columns = request.args.get('columns', '').split(',') if request.args.get('columns') else None

        conn = get_db_connection()
        query = f"SELECT * FROM {table_real}"
        if selected_columns and selected_columns[0]:
            query = f"SELECT {', '.join(selected_columns)} FROM {table_real}"

        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(column_names)
        writer.writerows(rows)

        output.seek(0)
        buffer = io.BytesIO()
        buffer.write(output.getvalue().encode('utf-8'))
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='text/csv',
            as_attachment=True,
            download_name=safe_filename(table_real, 'csv')
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_import_bp.route('/export/txt/<table>')
def export_txt(table):
    try:
        table_real = resolve_table(table)
        if not table_exists(table_real):
            return jsonify({'error': f'No existe la tabla {table_real}'}), 404
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_real}")
        rows = cursor.fetchall()
        column_names = [description[0] for description in cursor.description]
        conn.close()

        output = io.StringIO()
        output.write(f"REPORTE DE {table.upper()}\n")
        output.write("=" * 50 + "\n\n")

        for row in rows:
            for i, col in enumerate(column_names):
                output.write(f"{col}: {row[i]}\n")
            output.write("-" * 30 + "\n")

        output.seek(0)
        buffer = io.BytesIO()
        buffer.write(output.getvalue().encode('utf-8'))
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='text/plain',
            as_attachment=True,
            download_name=safe_filename(table_real, 'txt')
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def export_image(table):
    """
    Genera una imagen PNG con los primeros registros de la tabla.
    Sirve como respaldo cuando se pide ``export/image`` desde la UI.
    """
    try:
        table_real = resolve_table(table)
        if not table_exists(table_real):
            return jsonify({'error': f'No existe la tabla {table_real}'}), 404

        conn = get_db_connection()
        df = pd.read_sql_query(f"SELECT * FROM {table_real} LIMIT 25", conn)
        conn.close()

        if df.empty:
            return jsonify({'error': 'La tabla no contiene registros'}), 404

        # Limitar columnas para que no se desborde
        max_columns = 8
        columns = df.columns.tolist()[:max_columns]
        rows = df[columns].fillna('').astype(str).values.tolist()

        font = ImageFont.load_default()
        padding = 10
        col_width = 170
        header_height = 32
        row_height = 26
        width = col_width * len(columns) + padding * 2
        height = header_height + row_height * (len(rows) or 1) + padding * 2

        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)

        # Dibujar encabezados
        for idx, col in enumerate(columns):
            x = padding + idx * col_width
            draw.rectangle([x, padding, x + col_width - 5, padding + header_height], fill="#343a40")
            draw.text((x + 6, padding + 8), col, fill="white", font=font)

        # Filas
        for row_idx, row in enumerate(rows):
            y = padding + header_height + row_idx * row_height
            bg = "#f8f9fa" if row_idx % 2 == 0 else "#ffffff"
            draw.rectangle([padding, y, width - padding, y + row_height], fill=bg)
            for col_idx, cell in enumerate(row):
                x = padding + col_idx * col_width
                draw.text((x + 6, y + 6), str(cell), fill="black", font=font)

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype="image/png",
            as_attachment=True,
            download_name=safe_filename(table_real, "png")
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_import_bp.route('/export/barcode/<item_id>')
def generate_barcode(item_id):
    try:
        buffer = _build_barcode_image(item_id)
        return send_file(
            buffer,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'barcode_{item_id}.png'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_import_bp.route('/export/life_sheet/<item_id>')
def generate_life_sheet(item_id):
    if not item_id:
        return jsonify({'error': 'Indica un ID válido en la URL para generar la hoja de vida.'}), 400
    try:
        # Permitir override de tabla por query param; fallback a individuales si equipos no existe
        table_param = request.args.get("table")
        table_real = resolve_table(table_param) if table_param else "equipos"
        if not table_exists(table_real):
            if table_exists("equipos_individuales"):
                table_real = "equipos_individuales"
            else:
                return jsonify({'error': f'No existe la tabla {table_real}'}), 404
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_real} WHERE id = ?", (item_id,))
        item = cursor.fetchone()
        column_names = [description[0] for description in cursor.description]
        conn.close()

        if not item:
            return jsonify({'error': 'Item not found'}), 404

        # Create PDF life sheet
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        styles = getSampleStyleSheet()

        # Title
        title = Paragraph("HOJA DE VIDA DEL EQUIPO", styles['Title'])
        elements.append(title)

        # Equipment details
        details = []
        for i, col in enumerate(column_names):
            details.append([col.upper(), str(item[i])])

        table = Table(details)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), '#343a40'),
            ('TEXTCOLOR', (0, 0), (0, -1), '#ffffff'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, '#000000'),
        ]))

        elements.append(table)
        doc.build(elements)

        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=safe_filename(f'hoja_vida_{item_id}', 'pdf')
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_import_bp.route('/import/excel/<table>', methods=['POST'])
def import_excel(table):
    try:
        table_real = resolve_table(table)
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':


            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            return jsonify({'error': 'Invalid file format. Only .xlsx, .xls, and .csv files are allowed'}), 400

        # Read the file into a DataFrame
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Map column names to database fields
        column_mapping = get_column_mapping(table_real)
        df.rename(columns=column_mapping, inplace=True)

        # Insert data into database
        imported_count = 0
        for _, row in df.iterrows():
            try:
                if table_real == 'inventarios':
                    cursor.execute("""
                        INSERT INTO equipos (codigo_activo, serial, tipo_equipo, marca, modelo, estado, sede_id, observaciones)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('codigo_activo', ''),
                        row.get('serial', ''),
                        row.get('tipo_equipo', 'Computador'),
                        row.get('marca', ''),
                        row.get('modelo', ''),
                        row.get('estado', 'disponible'),
                        row.get('sede_id', 1),
                        row.get('observaciones', '')
                    ))
                elif table_real == 'users':
                    cursor.execute("""
                        INSERT INTO usuarios (cedula, nombre, apellido, email, documento, estado)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('cedula', ''),
                        row.get('nombre', ''),
                        row.get('apellido', ''),
                        row.get('email', ''),
                        row.get('documento', ''),
                        row.get('estado', 'activo')
                    ))
                elif table_real == 'licencias_office365':
                    cursor.execute("""
                        INSERT INTO licencias_office365 (usuario, email, estado, sede_id)
                        VALUES (?, ?, ?, ?)
                    """, (
                        row.get('usuario', ''),
                        row.get('email', ''),
                        row.get('estado', 'activo'),
                        row.get('sede_id', 1)
                    ))
                else:
                    # Para tablas no mapeadas, usar to_sql directo
                    df.to_sql(table_real, conn, if_exists='append', index=False)
                imported_count += 1
            except Exception as row_error:
                # Log individual row errors but continue with other rows
                print(f"Error importing row: {row_error}")
                continue

        conn.commit()
        conn.close()

        return jsonify({'message': f'Successfully imported {imported_count} records into {table_real}'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_import_bp.route('/import/json/<table>', methods=['POST'])
def import_json(table):
    try:
        table_real = resolve_table(table)
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith('.json'):
            return jsonify({'error': 'Invalid file format. Only .json files are allowed'}), 400

        # Read JSON file
        data = json.load(file)

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Insert data into database
        conn = get_db_connection()
        df.to_sql(table_real, conn, if_exists='append', index=False)
        conn.close()

        return jsonify({
            'message': f'Successfully imported {len(df)} records from JSON',
            'columns': list(df.columns),
            'rows': len(df)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_import_bp.route('/import/formatos/<filename>')
def import_from_formatos(filename):
    try:
        formatos_path = os.path.join(current_app.root_path, 'formatos', filename)

        if not os.path.exists(formatos_path):
            return jsonify({'error': f'File {filename} not found in formatos folder'}), 404

        # Read Excel file from formatos folder
        df = pd.read_excel(formatos_path)

        # Insert data into database (adapted to WorkManager schema - equipos table)
        table_name = 'equipos'  # Use equipos table for inventory

        conn = get_db_connection()
        df.to_sql(table_name, conn, if_exists='append', index=False)
        conn.close()

        return jsonify({
            'message': f'Successfully imported {len(df)} records from {filename}',
            'columns': list(df.columns),
            'rows': len(df),
            'file': filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_import_bp.route('/list/formatos')
def list_formatos_files():
    try:
        formatos_path = os.path.join(current_app.root_path, 'formatos')
        if not os.path.exists(formatos_path):
            return jsonify({'files': []})

        files = []
        for file in os.listdir(formatos_path):
            if file.endswith(('.xlsx', '.xls', '.csv')):
                file_path = os.path.join(formatos_path, file)
                file_size = os.path.getsize(file_path)
                files.append({
                    'name': file,
                    'size': file_size,
                    'path': f'/formatos/{file}'
                })

        return jsonify({'files': files})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_import_bp.route('/import/csv/<table>', methods=['POST'])
def import_csv(table):
    try:
        table_real = resolve_table(table)
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Invalid file format'}), 400

        # Read CSV file
        df = pd.read_csv(file)

        # Insert data into database
        conn = get_db_connection()
        df.to_sql(table_real, conn, if_exists='append', index=False)
        conn.close()

        return jsonify({
            'message': f'Successfully imported {len(df)} records',
            'columns': list(df.columns),
            'rows': len(df)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_import_bp.route('/import/universal', methods=['POST'])
def import_universal():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        table = resolve_table(request.form.get('table', 'inventarios'))

        # Detect file type and read accordingly
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            return jsonify({'error': 'Unsupported file format'}), 400

        # AI-powered column detection (simplified)
        detected_columns = detect_columns_ai(df.columns.tolist())

        # Insert data
        conn = get_db_connection()
        df.to_sql(table, conn, if_exists='append', index=False)
        conn.close()

        return jsonify({
            'message': f'Imported {len(df)} records using AI column detection',
            'detected_columns': detected_columns,
            'rows': len(df)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@export_import_bp.route('/export/life_sheet/')
def life_sheet_help():
    """
    Ruta auxiliar para cuando se solicita /export/life_sheet/ sin un ID.
    Devuelve mensaje más amigable.
    """
    return jsonify({
        'error': 'Debes indicar el ID del equipo (por ejemplo /export_import/export/life_sheet/123) para bajar la hoja de vida.'
    }), 400


def _deduplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Garantiza que las columnas sean únicas para evitar errores de reindexado
    al concatenar múltiples archivos.
    """
    seen = {}
    new_cols = []
    for col in df.columns:
        base = str(col).strip() or "col"
        count = seen.get(base, 0)
        # Añadir sufijo solo a partir del segundo duplicado para preservar el encabezado original
        new_name = f"{base}_{count+1}" if count else base
        seen[base] = count + 1
        new_cols.append(new_name)
    cleaned = df.copy()
    cleaned.columns = new_cols
    return cleaned

def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia encabezados y celdas: elimina BOM, espacios y filas vacías.
    """
    cleaned = df.copy()
    cleaned.columns = [str(c).replace("\ufeff", "").strip() for c in cleaned.columns]
    # Usar índice para evitar conflicto con columnas duplicadas que devolverían DataFrame
    for idx, col in enumerate(cleaned.columns):
        series = cleaned.iloc[:, idx]
        if series.dtype == object:
            cleaned.iloc[:, idx] = (
                series.astype(str)
                .str.replace("\ufeff", "", regex=False)
                .str.strip()
            )
    cleaned = cleaned.dropna(how="all")
    return cleaned

@export_import_bp.route('/importador', methods=['GET'])
def importar_form():
    return render_template(
        "importador_universal.html",
        modules=MODULES,
        export_formats=EXPORT_FORMATS,
        target="auto",
        detected_target=None,
        headers=None,
        preview_rows=None,
        tmp_file=None,
        file_previews=[],
        combined_shape={"rows": 0, "cols": 0},
    )

# Compatibilidad con rutas antiguas
@export_import_bp.route('/export_import/importador', methods=['GET'])
@export_import_bp.route('/export_import/importador/', methods=['GET'])
def importar_form_legacy():
    return redirect(url_for("export_import_v2.importar_form"))


@export_import_bp.route('/importador/preview', methods=['POST'])
def importar_preview():
    target = request.form.get("target", "auto")

    # Permitir varios archivos a la vez; si no hay lista, intentar con el campo legacy "file"
    uploaded_files = [f for f in request.files.getlist("files") if f and f.filename]
    if not uploaded_files:
        legacy = request.files.get("file")
        if legacy and legacy.filename:
            uploaded_files = [legacy]

    if not uploaded_files:
        flash("Debes seleccionar al menos un archivo CSV o Excel.", "danger")
        return redirect(url_for("export_import_v2.importar_form"))

    dataframes = []
    saved_paths = []
    errors = []
    file_previews = []

    seen_headers = set()
    for f in uploaded_files:
        tmp_name = f"import_{int(time.time() * 1000)}_{secure_filename(f.filename)}"
        tmp_path = os.path.join(TMP_DIR, tmp_name)
        f.save(tmp_path)
        saved_paths.append(tmp_path)
        try:
            loaded_frames = load_dataframes(tmp_path)
            for df in loaded_frames:
                cleaned = _clean_dataframe(df)
                header_key = tuple(cleaned.columns)
                if header_key in seen_headers:
                    continue  # evita duplicar mismas columnas de varias hojas
                seen_headers.add(header_key)
                dataframes.append(_deduplicate_columns(cleaned))
                file_previews.append({
                    "name": f.filename,
                    "rows": len(cleaned),
                    "cols": len(cleaned.columns),
                    "headers": list(cleaned.columns)[:10],
                })
        except Exception as e:
            errors.append(f"{f.filename}: {e}")

    if errors:
        flash("Algunos archivos tuvieron problemas de lectura: " + "; ".join(errors), "warning")

    if not dataframes:
        flash("El archivo no contiene datos legibles.", "warning")
        return redirect(url_for("export_import_v2.importar_form"))

    combined_df = pd.concat(dataframes, ignore_index=True)
    headers = list(combined_df.columns)
    mapping, norm_headers = build_column_mapping(headers)
    mapping = _apply_ai_mapping(headers, mapping)
    if target == "auto" or not target:
        target = detect_target_from_headers(norm_headers)

    # Persistimos un archivo combinado para el paso de procesamiento
    if len(saved_paths) == 1:
        tmp_name = os.path.basename(saved_paths[0])
    else:
        tmp_name = f"import_combo_{int(time.time())}.csv"
        tmp_path = os.path.join(TMP_DIR, tmp_name)
        combined_df.to_csv(tmp_path, index=False)

    if len(uploaded_files) > 1:
        flash(f"Se cargaron {len(uploaded_files)} archivos. Se combinaron para la vista previa y el procesamiento.", "info")

    preview_rows = combined_df.head(10).to_dict(orient="records")

    return render_template(
        "importador_universal.html",
        modules=MODULES,
        export_formats=EXPORT_FORMATS,
        tmp_file=tmp_name,
        target=target,
        headers=headers,
        # La clave: enviamos el mapeo sugerido a la plantilla
        column_mapping=mapping,
        preview_rows=preview_rows,
        detected_target=target,
        file_previews=file_previews,
        combined_shape={"rows": len(combined_df), "cols": len(combined_df.columns)},
    )


@export_import_bp.route('/importador/preview_folder', methods=['POST'])
def importar_preview_folder():
    """
    Analiza una carpeta completa de archivos, los combina y presenta una vista previa para mapeo.
    Similar a la funcionalidad "Get Data from Folder" de Power BI.
    """
    folder_alias = request.form.get("folder_source")
    target = request.form.get("target", "auto")
    if not folder_alias:
        flash("Debes seleccionar una carpeta de origen.", "danger")
        return redirect(url_for("export_import_v2.importar_form"))

    source_folders = {
        "uploads": os.path.join(current_app.root_path, "uploads"),
        "tmp_imports": os.path.join(current_app.root_path, "tmp_imports"),
        "inventario_tecnologico": os.path.join(current_app.root_path, "inventarios", "equipos tecnologicos")
    }
    source_folders.update(current_app.config.get("IMPORT_FOLDERS", {}))

    folder_path = source_folders.get(folder_alias)

    if not folder_path or not os.path.isdir(folder_path):
        flash(f"La carpeta de origen '{folder_alias}' no existe o no est? configurada.", "danger")
        return redirect(url_for("export_import_v2.importar_form"))

    allowed_ext = (".csv", ".xls", ".xlsx")
    files = [f for f in os.listdir(folder_path) if f.lower().endswith(allowed_ext)]
    if not files:
        flash("La carpeta no contiene archivos CSV/Excel para importar.", "warning")
        return redirect(url_for("export_import_v2.importar_form"))

    dataframes = []
    file_previews = []
    errors = []

    seen_headers = set()
    for name in files:
        path = os.path.join(folder_path, name)
        try:
            loaded_frames = load_dataframes(path)
            for df in loaded_frames:
                cleaned = _clean_dataframe(df)
                header_key = tuple(cleaned.columns)
                if header_key in seen_headers:
                    continue
                seen_headers.add(header_key)
                dataframes.append(_deduplicate_columns(cleaned))
                file_previews.append({
                    "name": name,
                    "rows": len(cleaned),
                    "cols": len(cleaned.columns),
                    "headers": list(cleaned.columns)[:10],
                })
        except Exception as e:
            errors.append(f"{name}: {e}")

    if errors:
        flash("Algunos archivos tuvieron problemas de lectura: " + "; ".join(errors), "warning")

    if not dataframes:
        flash("No se encontraron datos legibles en la carpeta.", "warning")
        return redirect(url_for("export_import_v2.importar_form"))

    combined_df = pd.concat(dataframes, ignore_index=True)
    headers = list(combined_df.columns)
    mapping, norm_headers = build_column_mapping(headers)
    mapping = _apply_ai_mapping(headers, mapping)
    if target == "auto" or not target:
        target = detect_target_from_headers(norm_headers)

    tmp_name = f"folder_import_{int(time.time())}.csv"
    tmp_path = os.path.join(TMP_DIR, tmp_name)
    combined_df.to_csv(tmp_path, index=False)

    preview_rows = combined_df.head(10).to_dict(orient="records")

    return render_template(
        "importador_universal.html",
        modules=MODULES,
        export_formats=EXPORT_FORMATS,
        tmp_file=tmp_name,
        target=target,
        headers=headers,
        column_mapping=mapping,
        preview_rows=preview_rows,
        detected_target=target,
        file_previews=file_previews,
        combined_shape={"rows": len(combined_df), "cols": len(combined_df.columns)},
    )

# Aquí iría la lógica para combinar archivos y generar la vista previa, similar a importar_preview
    return redirect(url_for("export_import_v2.importar_form"))


@export_import_bp.route('/importador/procesar', methods=['POST'])
def importar_procesar():
    tmp_file = request.form.get("tmp_file")
    target = request.form.get("target")
    user_mapping = {key: request.form[key] for key in request.form if key.startswith('map-')}
    selected_columns_raw = request.form.get("selected_columns") or ""
    selected_columns = [c for c in selected_columns_raw.split(",") if c.strip()]

    if not tmp_file or not target:
        flash("Sesión de importación no válida.", "danger")
        return redirect(url_for("export_import_v2.importar_form"))

    tmp_path = os.path.join(TMP_DIR, tmp_file)
    if not os.path.exists(tmp_path):
        flash("El archivo temporal ya no existe. Vuelve a subir el archivo.", "danger")
        return redirect(url_for("export_import_v2.importar_form"))

    try:
        dataframes = load_dataframes(tmp_path)
    except Exception as e:
        flash(f"Error leyendo el archivo: {e}", "danger")
        return redirect(url_for("export_import_v2.importar_form"))

    total_inserted = 0
    total_updated = 0
    total_staged = 0
    all_errors = []

    for df in dataframes:
        df = _clean_dataframe(df)
        if selected_columns:
            usable_cols = [c for c in selected_columns if c in df.columns]
            if usable_cols:
                df = df[usable_cols]
        headers = list(df.columns)
        # Usar el mapeo del usuario si está disponible; completar con autodetección.
        # Si una columna queda sin mapear, se envía como None para que se guarde en import_unmapped.
        auto_mapping, norm_headers = build_column_mapping(headers)
        final_mapping = {}
        for i, header in enumerate(headers):
            user_choice = user_mapping.get(f"map-{i}", "").strip()
            if user_choice:
                final_mapping[header] = user_choice  # elección explícita del usuario
            else:
                final_mapping[header] = auto_mapping.get(header)  # puede ser None y se usará para staging

        current_target = detect_target_from_headers(norm_headers) if target == "auto" else target
        inserted, updated, errors, staged = import_rows(df, current_target, final_mapping, source=tmp_file)
        total_inserted += inserted
        total_updated += updated
        total_staged += staged
        all_errors.extend(errors)

    try:
        os.remove(tmp_path)
    except Exception:
        pass

    flash(f"Importación completada. Nuevos: {total_inserted}, Actualizados: {total_updated}.", "success")
    if all_errors:
        flash(f"{len(all_errors)} advertencias / errores. Ejemplo:", "warning")
        for e in all_errors[:5]:
            flash(e, "warning")
    if total_staged:
        flash(f"{total_staged} filas guardadas con columnas no mapeadas (staging import_unmapped). Ajusta el mapeo o revisa esos datos.", "info")
    try:
        _log_import_summary(target, total_inserted, total_updated, len(all_errors), tmp_file, total_staged)
    except Exception as e:
        flash(f"No se pudo registrar el log de importaciA3n: {e}", "warning")

    return redirect(url_for("export_import_v2.importar_form"))


def _log_import_summary(target: str, inserted: int, updated: int, errors: int, source: str = "", staged: int = 0):
    """Registra la sesiA3n de importaciA3n en una tabla local para consultas de estado."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS import_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT,
            inserted INTEGER,
            updated INTEGER,
            errors INTEGER,
            staged INTEGER,
            source TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    try:
        cur.execute("ALTER TABLE import_logs ADD COLUMN staged INTEGER")
    except Exception:
        pass
    cur.execute(
        "INSERT INTO import_logs (target, inserted, updated, errors, staged, source) VALUES (?, ?, ?, ?, ?, ?)",
        (target, inserted, updated, errors, staged, source),
    )
    conn.commit()
    conn.close()


def _apply_ai_mapping(headers, mapping):
    """
    Enriquecemos el mapping usando IA si hay columnas no mapeadas.
    Prioridad: OpenAI -> Groq -> heuristica local.
    """
    if not headers:
        return mapping
    missing = [h for h, v in mapping.items() if v is None]
    if not missing:
        return mapping
    suggestions = {}
    # Intentar OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")
    prompt = (
        "Dada la lista de encabezados de un archivo de inventario/empleados/licencias/bajas/insumos, "
        "devuelve un JSON mapping de cada encabezado a un campo canonico: "
        "inventario:[serial,codigo_barras_individual,placa,modelo,marca,procesador,ram,ip,hostname,estado,ubicacion,tecnologia], "
        "licencias:[email,tipo_licencia,usuario_lic], empleados:[cedula,nombre,apellido,nombre_completo,email], "
        "bajas:[motivo_baja,responsable_baja,tipo_inventario], insumos:[nombre_insumo,cantidad_total,ubicacion,asignado_a]. "
        "No inventes columnas fuera de esos conjuntos. Responde solo JSON plano sin comentario."
    )
    try:
        if openai_key:
            import openai

            client = openai.OpenAI(api_key=openai_key)
            resp = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": pyjson.dumps(headers, ensure_ascii=False)},
                ],
                max_tokens=300,
                temperature=0,
            )
            txt = resp.choices[0].message.content
            suggestions = pyjson.loads(txt)
        elif groq_key:
            import groq

            client = groq.Client(api_key=groq_key)
            resp = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": pyjson.dumps(headers, ensure_ascii=False)},
                ],
                max_tokens=300,
                temperature=0,
            )
            txt = resp.choices[0].message.content
            suggestions = pyjson.loads(txt)
    except Exception:
        suggestions = {}

    # Heuristica local como fallback
    if not suggestions:
        for h in headers:
            low = h.lower()
            # Heurística conservadora: solo mapeos fuertes para evitar asignaciones erróneas
            if "serial" in low or "eserial" == low:
                suggestions[h] = "serial"
            elif "placa" in low or "codigo unificado" in low or "codigo individual" in low:
                suggestions[h] = "codigo_barras_individual"
            elif "imei" in low:
                suggestions[h] = "imei"
            elif "procesador" in low or "cpu" in low:
                suggestions[h] = "procesador"
            elif "ram" in low and "arquitectura" not in low:
                suggestions[h] = "ram"
            elif "email" in low or "correo" in low:
                suggestions[h] = "email"
            elif "cedula" in low or "documento" in low:
                suggestions[h] = "cedula"
            elif "nombre" in low and ("parte" in low or "insumo" in low or "articulo" in low):
                suggestions[h] = "nombre_insumo"
            elif "cantidad" in low and ("insumo" in low or "parte" in low or "articulo" in low):
                suggestions[h] = "cantidad_total"
            elif "tecnologia" in low:
                suggestions[h] = "tecnologia"
            elif "asignado" in low:
                suggestions[h] = "asignado_a"
            elif "ubicacion" in low or "sede" in low or "area" in low:
                suggestions[h] = "ubicacion"
            elif "motivo" in low and "baja" in low:
                suggestions[h] = "motivo_baja"
            elif "responsable" in low and "baja" in low:
                suggestions[h] = "responsable_baja"
            elif "observacion" in low:
                suggestions[h] = "observaciones"
            elif low == "proveedor":
                suggestions[h] = "proveedor"

    # Mezclar con mapping existente solo donde faltaba
    for h in headers:
        if mapping.get(h) is None and h in suggestions:
            mapping[h] = suggestions[h]
    return mapping


@export_import_bp.route('/importador/status', methods=['GET'])
def import_status():
    """Devuelve estado reciente de importaciones y conteo de tablas para refrescar tabs."""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT target, inserted, updated, errors, staged, source, created_at
            FROM import_logs
            ORDER BY created_at DESC
            LIMIT 5
            """
        )
        logs = [dict(zip([col[0] for col in cur.description], row)) for row in cur.fetchall()]
    except Exception:
        logs = []

    table_counts = []
    try:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cur.fetchall()]
        for name in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {name}")
                count = cur.fetchone()[0]
            except Exception:
                count = None
            table_counts.append({"table": name, "rows": count})
    except Exception:
        table_counts = []

    conn.close()
    return jsonify({"logs": logs, "tables": table_counts})


@export_import_bp.route('/importador/unmapped.csv', methods=['GET'])
def export_unmapped():
    """Descarga en CSV las filas con columnas no mapeadas."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT target, source, row_index, payload, created_at
            FROM import_unmapped
            ORDER BY created_at DESC
            """
        )
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["target", "source", "row_index", "payload", "created_at"])
    for row in rows:
        writer.writerow(list(row))
    output.seek(0)
    buffer = io.BytesIO()
    buffer.write(output.getvalue().encode("utf-8-sig"))
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="text/csv",
        as_attachment=True,
        download_name="import_unmapped.csv"
    )


@export_import_bp.route('/importador/unmapped', methods=['GET'])
def list_unmapped():
    """Devuelve las filas staging con columnas no mapeadas (JSON para la UI)."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS import_unmapped (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                source TEXT,
                row_index INTEGER,
                payload TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cur.execute(
            """
            SELECT id, target, source, row_index, payload, created_at
            FROM import_unmapped
            ORDER BY created_at DESC
            LIMIT 200
            """
        )
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"rows": rows})

def detect_columns_ai(columns):
    """Simple AI-powered column detection"""
    mapping = {}
    for col in columns:
        col_lower = col.lower()
        if 'id' in col_lower:
            mapping[col] = 'id'
        elif 'name' in col_lower or 'nombre' in col_lower:
            mapping[col] = 'name'
        elif 'model' in col_lower or 'modelo' in col_lower:
            mapping[col] = 'model'
        elif 'serial' in col_lower:
            mapping[col] = 'serial'
        elif 'user' in col_lower or 'usuario' in col_lower:
            mapping[col] = 'user_id'
        elif 'status' in col_lower or 'estado' in col_lower:
            mapping[col] = 'status'
        else:
            mapping[col] = col_lower.replace(' ', '_')

    return mapping


def resolve_table(table: str) -> str:
    """Mapea alias amigables a tablas reales."""
    if not table:
        return table
    return TABLE_ALIASES.get(table, table)


def _build_barcode_image(code_value: str) -> io.BytesIO:
    """
    Genera un PNG de codigo de barras. Usa python-barcode si esta disponible,
    de lo contrario crea una imagen simple con Pillow para no fallar.
    """
    buf = io.BytesIO()
    if BARCODE_AVAILABLE:
        code = Code128(str(code_value), writer=ImageWriter())
        code.write(buf, options={"write_text": True, "text_distance": 1})
        buf.seek(0)
        return buf

    # Fallback manual con Pillow
    width, height = 400, 160
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    # Dibujar bandas simples para simular codigo
    num_bars = 50
    margin = 20
    bar_width = (width - 2 * margin) / num_bars
    for i in range(num_bars):
        if i % 2 == 0:
            x0 = margin + i * bar_width
            draw.rectangle([x0, margin, x0 + bar_width * 0.7, height - margin * 2], fill="black")

    # Texto legible
    text = str(code_value)
    try:
        font = ImageFont.load_default()
        text_w, text_h = draw.textsize(text, font=font)
    except Exception:
        font = None
        text_w, text_h = (len(text) * 8, 14)
    draw.text(((width - text_w) / 2, height - margin), text, fill="black", font=font)

    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def table_exists(table_name: str) -> bool:
    """Verifica si existe la tabla en la base de datos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def get_column_mapping(table):
    """Get column mapping for different tables"""
    if table == 'inventarios':
        return {
            'Código Activo': 'codigo_activo',
            'Serial': 'serial',
            'Tipo de Equipo': 'tipo_equipo',
            'Marca': 'marca',
            'Modelo': 'modelo',
            'Estado': 'estado',
            'Sede': 'sede_id',
            'Observaciones': 'observaciones',
            'Procesador': 'procesador',
            'RAM': 'ram',
            'Disco Duro': 'disco_duro',
            'Sistema Operativo': 'sistema_operativo',
            'Fecha de Compra': 'fecha_compra',
            'Valor de Compra': 'valor_compra'
        }
    elif table == 'users':
        return {
            'Cédula': 'cedula',
            'Nombre': 'nombre',
            'Apellido': 'apellido',
            'Email': 'email',
            'Documento': 'documento',
            'Estado': 'estado'
        }
    elif table == 'licencias_office365':
        return {
            'Usuario': 'usuario',
            'Email': 'email',
            'Estado': 'estado',
            'Sede': 'sede_id'
        }
    return {}

@export_import_bp.route('/search/users/<query>')
def search_users(query):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Search by ID, name, email, or document (adapted to WorkManager schema)
        cursor.execute("""
            SELECT id, nombre, email, documento
            FROM usuarios
            WHERE id LIKE ? OR nombre LIKE ? OR email LIKE ? OR documento LIKE ?
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))

        users = cursor.fetchall()
        conn.close()

        return jsonify([dict(user) for user in users])

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_import_bp.route('/assign/equipment', methods=['POST'])
def assign_equipment():
    try:
        data = request.get_json()
        equipment_id = data['equipment_id']
        user_id = data['user_id']
        assignment_date = data['assignment_date']
        notes = data.get('notes', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Update equipment with user assignment (adapted to WorkManager schema)
        cursor.execute("""
            UPDATE equipos
            SET usuario_asignado = ?, estado = 'asignado', observaciones = ?
            WHERE id = ?
        """, (user_id, notes, equipment_id))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Equipment assigned successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@export_import_bp.route('/get_columns/<table>')
def get_columns(table):
    """Get column names for a table"""
    try:
        table_real = resolve_table(table)
        if not table_exists(table_real):
            return jsonify({'error': f'No existe la tabla {table_real}'}), 404
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get column names
        cursor.execute(f"PRAGMA table_info({table_real})")
        columns_info = cursor.fetchall()
        conn.close()

        columns = [col[1] for col in columns_info]  # Column name is at index 1

        return jsonify({'columns': columns})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------- Rutas de exportacion unificadas ----------
@export_import_bp.route('/export/<fmt>/<table>', methods=['GET'])
def export_dispatch(fmt, table):
    """Despacha export segun formato."""
    fmt = fmt.lower()
    if fmt == 'excel':
        return export_excel(table)
    if fmt == 'json':
        return export_json(table)
    if fmt == 'pdf':
        return export_pdf(table)
    if fmt == 'csv':
        return export_csv(table)
    if fmt == 'txt':
        return export_txt(table)
    if fmt == 'barcode':
        return generate_barcode(table)
    if fmt == 'life_sheet':
        return generate_life_sheet(table)
    if fmt == 'image':
        return export_image(table)
    return jsonify({'error': f'Formato {fmt} no soportado'}), 400


def safe_filename(name: str, ext: str) -> str:
    """Normaliza nombres de archivo para headers HTTP."""
    base = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    sanitized = "".join(c for c in base if c not in ["\n", "\r", "\t", '"', "'", ";"])
    return f"{sanitized}.{ext}"


@export_import_bp.route('/tables', methods=['GET'])
def list_tables():
    """Lista tablas disponibles con conteo de filas (util para UI)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    result = []
    for name in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {name}")
            count = cursor.fetchone()[0]
        except Exception:
            count = None
        result.append({"table": name, "rows": count})
    conn.close()
    return jsonify(result)
