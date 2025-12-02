from flask import Blueprint, request, Response, flash, redirect, url_for
import sqlite3
import pandas as pd
import io
from datetime import datetime

universal_exporter_bp = Blueprint('universal_exporter', __name__, url_prefix='/export')

def get_db_connection():
    conn = sqlite3.connect('workmanager_erp.db')
    conn.row_factory = sqlite3.Row
    return conn

# Configuración de qué se puede exportar
EXPORT_CONFIG = {
    'licencias': {
        'query': "SELECT l.usuario_asignado, l.email, l.tipo_licencia, l.estado, l.fecha_asignacion, e.cedula, e.cargo, e.departamento FROM licencias_office365 l LEFT JOIN empleados e ON (LOWER(e.correo_office) = LOWER(l.email))",
        'filename': 'licencias'
    },
    'empleados': {
        'query': "SELECT nombre_completo, cedula, cargo, departamento, email, telefono, estado, fecha_ingreso FROM empleados",
        'filename': 'empleados'
    },
    'inventario_tecnologico': {
        'query': "SELECT nombre_equipo, marca, modelo, serial, estado, fecha_compra, (SELECT nombre FROM sedes s WHERE s.id = ei.sede_id) as sede FROM equipos_individuales ei",
        'filename': 'inventario_tecnologico'
    },
    'inventario_biomedico': {
        'query': "SELECT nombre_equipo, marca, modelo, serie, estado, ubicacion FROM equipos_biomedicos",
        'filename': 'inventario_biomedico'
    },
    'solicitudes': {
        'query': "SELECT s.tipo_solicitud, s.estado, s.fecha_creacion, e.nombre_completo as empleado, s.descripcion FROM solicitudes s JOIN empleados e ON s.empleado_id = e.id",
        'filename': 'solicitudes'
    }
}

@universal_exporter_bp.route('/<string:data_source>/<string:file_format>')
def export_data(data_source, file_format):
    """
    Exportador universal.
    Ej: /export/licencias/excel
    Ej: /export/empleados/csv
    """
    if data_source not in EXPORT_CONFIG:
        flash(f"Fuente de datos '{data_source}' no es exportable.", 'danger')
        return redirect(request.referrer or url_for('index'))

    config = EXPORT_CONFIG[data_source]
    conn = get_db_connection()
    
    try:
        # Aquí se podrían añadir filtros basados en request.args si se quisiera
        df = pd.read_sql_query(config['query'], conn)
        
        output = io.BytesIO()
        filename = f"{config['filename']}_{datetime.now().strftime('%Y%m%d')}"

        if file_format == 'excel':
            df.to_excel(output, index=False, sheet_name=data_source)
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename += '.xlsx'
        elif file_format == 'csv':
            df.to_csv(output, index=False, encoding='utf-8-sig')
            mimetype = 'text/csv'
            filename += '.csv'
        else:
            flash(f"Formato de archivo '{file_format}' no soportado.", "danger")
            return redirect(request.referrer or url_for('index'))

        output.seek(0)

        return Response(
            output,
            mimetype=mimetype,
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    except Exception as e:
        flash(f"Error al exportar los datos: {e}", "danger")
        return redirect(request.referrer or url_for('index'))
    finally:
        conn.close()