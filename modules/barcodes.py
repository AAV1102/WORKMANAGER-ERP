from flask import Blueprint, render_template, request, Response, flash, redirect, url_for
from flask_login import login_required
import sqlite3
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import barcode
from barcode.writer import ImageWriter

barcodes_bp = Blueprint('barcodes', __name__, url_prefix='/barcodes', template_folder='../templates')

def get_db_connection():
    conn = sqlite3.connect('workmanager_erp.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- CONFIGURACIÓN CENTRAL DE ACTIVOS PARA CÓDIGOS DE BARRAS ---
ASSET_CONFIG = {
    'equipos_tecnologicos': {
        'display_name': 'Equipos Tecnológicos',
        'table': 'equipos_individuales',
        'id_col': 'id',
        'search_fields': ['codigo_barras_individual', 'serial', 'marca', 'modelo', 'nombre_equipo'],
        'barcode_field': 'codigo_barras_individual',
        'display_fields': ['marca', 'modelo', 'serial'],
    },
    'equipos_biomedicos': {
        'display_name': 'Equipos Biomédicos',
        'table': 'equipos_biomedicos',
        'id_col': 'id',
        'search_fields': ['codigo_barras', 'serie', 'marca', 'modelo', 'nombre_equipo'],
        'barcode_field': 'codigo_barras',
        'display_fields': ['nombre_equipo', 'marca', 'modelo', 'serie'],
    },
    'usuarios': {
        'display_name': 'Usuarios / Empleados',
        'table': 'empleados',
        'id_col': 'id',
        'search_fields': ['cedula', 'nombre_completo', 'email', 'cargo'],
        'barcode_field': 'cedula',
        'display_fields': ['nombre_completo', 'cargo', 'departamento'],
    },
    'sedes': {
        'display_name': 'Sedes',
        'table': 'sedes',
        'id_col': 'id',
        'search_fields': ['nombre', 'direccion', 'ciudad'],
        'barcode_field': 'id',
        'display_fields': ['nombre', 'direccion', 'ciudad'],
    },
}

@barcodes_bp.route('/', methods=['GET'])
@login_required
def barcode_center():
    """Página principal del centro de códigos de barras."""
    asset_type = request.args.get('type', None)
    search_query = request.args.get('q', '')
    items = []
    config = None

    if asset_type and asset_type in ASSET_CONFIG:
        config = ASSET_CONFIG[asset_type]
        if search_query:
            conn = get_db_connection()
            conditions = " OR ".join([f"{field} LIKE ?" for field in config['search_fields']])
            query = f"SELECT * FROM {config['table']} WHERE {conditions} LIMIT 100"
            params = (f'%{search_query}%',) * len(config['search_fields'])
            try:
                items = conn.execute(query, params).fetchall()
            except sqlite3.OperationalError as e:
                flash(f"Error al buscar en la tabla '{config['table']}': {e}", 'danger')
            finally:
                conn.close()
    
    return render_template(
        'barcodes/center.html', 
        items=items, 
        search_query=search_query,
        asset_configs=ASSET_CONFIG,
        current_config=config,
        current_asset_type=asset_type
    )

@barcodes_bp.route('/generate_pdf', methods=['POST'])
@login_required
def generate_pdf():
    """Genera un PDF con los códigos de barras de los IDs seleccionados."""
    selected_ids = request.form.getlist('item_ids')
    asset_type = request.form.get('asset_type')

    if not selected_ids or not asset_type or asset_type not in ASSET_CONFIG:
        flash('No seleccionaste ningún ítem o el tipo de activo es inválido.', 'warning')
        return redirect(url_for('barcodes.barcode_center'))

    config = ASSET_CONFIG[asset_type]
    conn = get_db_connection()
    placeholders = ','.join('?' for _ in selected_ids)
    query = f"SELECT * FROM {config['table']} WHERE {config['id_col']} IN ({placeholders})"
    
    try:
        items = conn.execute(query, selected_ids).fetchall()
    except sqlite3.OperationalError as e:
        flash(f"Error al obtener datos de la tabla '{config['table']}': {e}", 'danger')
        return redirect(url_for('barcodes.barcode_center', type=asset_type))
    finally:
        conn.close()

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    label_width = 2.625 * inch
    label_height = 1 * inch
    left_margin = 0.18 * inch
    top_margin = 0.5 * inch
    x_gap = 0.14 * inch
    y_gap = 0
    cols = 3
    rows = 10
    x_pos = left_margin
    y_pos = height - top_margin - label_height
    
    c.setFont("Helvetica", 7)

    for i, item in enumerate(items):
        if i > 0 and i % (cols * rows) == 0:
            c.showPage() # Nueva página
            c.setFont("Helvetica", 7)
            x_pos = left_margin
            y_pos = height - top_margin - label_height

        # --- Dibuja la etiqueta ---
        barcode_value = str(item[config['barcode_field']]) if item[config['barcode_field']] else ''
        if not barcode_value: continue

        code128 = barcode.get_barcode_class('code128')
        code = code128(barcode_value, writer=ImageWriter())
        barcode_image = io.BytesIO()
        code.write(barcode_image)
        barcode_image.seek(0)

        c.drawImage(barcode_image, x_pos + 0.1 * inch, y_pos + 0.4 * inch, width=2.4 * inch, height=0.4 * inch, preserveAspectRatio=True)
        
        line1 = ' '.join(str(item.get(field, '')) for field in config['display_fields'][:2])
        line2 = ' '.join(str(item.get(field, '')) for field in config['display_fields'][2:])
        c.drawString(x_pos + 0.1 * inch, y_pos + 0.25 * inch, line1[:45]) # Limitar longitud
        c.drawString(x_pos + 0.1 * inch, y_pos + 0.15 * inch, line2[:45])
        c.drawCentredString(x_pos + label_width / 2, y_pos + 0.05 * inch, barcode_value)

        col_num = i % cols
        if col_num == cols - 1: # Última columna
            x_pos = left_margin
            y_pos -= (label_height + y_gap)
        else:
            x_pos += (label_width + x_gap)

    c.save()
    buffer.seek(0)

    return Response(buffer, mimetype='application/pdf', headers={
        'Content-Disposition': 'inline; filename=codigos_de_barras.pdf'
    })