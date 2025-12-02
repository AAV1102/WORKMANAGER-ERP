from flask import Blueprint, Response
from modules.db_utils import get_db_connection
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO
import datetime

report_generator_bp = Blueprint('report_generator', __name__)

@report_generator_bp.route('/report/inventory/pdf')
def generate_inventory_pdf():
    """
    Genera un informe en PDF del inventario de equipos individuales.
    """
    try:
        # 1. Obtener datos de la base de datos
        conn = get_db_connection()
        # Seleccionamos las columnas más relevantes para el informe
        equipos = conn.execute("""
            SELECT id, marca, modelo, serial, estado, asignado_nuevo, ciudad 
            FROM equipos_individuales 
            ORDER BY id
        """).fetchall()
        conn.close()

        # 2. Configurar el documento PDF en un buffer de memoria
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), topMargin=30, bottomMargin=30)
        
        elements = []
        styles = getSampleStyleSheet()

        # 3. Añadir título y fecha
        elements.append(Paragraph("Informe de Inventario de Equipos", styles['h1']))
        elements.append(Paragraph(f"Generado el: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # 4. Preparar los datos para la tabla
        headers = ["ID", "Marca", "Modelo", "Serial", "Estado", "Asignado A", "Ciudad"]
        data = [headers] + [[row[key] or 'N/A' for key in headers] for row in equipos]

        # 5. Crear y dar estilo a la tabla
        table = Table(data, repeatRows=1) # Repetir encabezados en cada página
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4e73df")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        table.setStyle(style)
        elements.append(table)

        doc.build(elements)
        buffer.seek(0)

        return Response(buffer, mimetype='application/pdf', headers={'Content-Disposition': 'inline;filename=informe_inventario.pdf'})

    except Exception as e:
        print(f"Error generando PDF: {e}")
        return "Error al generar el informe en PDF.", 500