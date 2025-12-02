from flask import Blueprint, render_template, abort
from flask_login import login_required
import sqlite3

asset_profile_bp = Blueprint('asset_profile', __name__, url_prefix='/asset_profile', template_folder='../templates')

def get_db_connection():
    conn = sqlite3.connect('workmanager_erp.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- CONFIGURACIÓN CENTRAL DE ACTIVOS ---
# Esta configuración define cómo buscar y relacionar datos para cada tipo de activo.
# La he movido aquí para que sea el "cerebro" de esta funcionalidad.
ASSET_CONFIG = {
    'equipos_tecnologicos': {
        'display_name': 'Equipo Tecnológico',
        'table': 'equipos_individuales',
        'id_col': 'id',
        'main_field': 'nombre_equipo',
        'relations': {
            'mantenimientos': {
                'display_name': 'Historial de Mantenimiento',
                'query': "SELECT * FROM mantenimientos WHERE equipo_id = ? ORDER BY fecha_mantenimiento DESC",
            },
            'asignaciones': {
                'display_name': 'Historial de Asignaciones',
                'query': """
                    SELECT a.*, e.nombre_completo as empleado FROM asignaciones a 
                    LEFT JOIN empleados e ON a.empleado_id = e.id
                    WHERE a.asset_type = 'equipos_tecnologicos' AND a.asset_id = ? ORDER BY a.fecha_asignacion DESC
                """,
            },
            'tickets': {
                'display_name': 'Tickets de Soporte',
                'query': "SELECT * FROM tickets WHERE asset_serial = (SELECT serial FROM equipos_individuales WHERE id = ?) ORDER BY fecha_creacion DESC",
            }
        }
    },
    'equipos_biomedicos': {
        'display_name': 'Equipo Biomédico',
        'table': 'equipos_biomedicos',
        'id_col': 'id',
        'main_field': 'nombre_equipo',
        'relations': {
            'mantenimientos': {
                'display_name': 'Historial de Mantenimiento Biomédico',
                'query': "SELECT * FROM mantenimientos_biomedicos WHERE equipo_id = ? ORDER BY fecha_mantenimiento DESC", # Asume tabla mantenimientos_biomedicos
            },
            'asignaciones': {
                'display_name': 'Historial de Asignaciones',
                'query': "SELECT a.*, e.nombre_completo as empleado FROM asignaciones a LEFT JOIN empleados e ON a.empleado_id = e.id WHERE a.asset_type = 'equipos_biomedicos' AND a.asset_id = ? ORDER BY a.fecha_asignacion DESC",
            },
             'calibraciones': {
                'display_name': 'Registros de Calibración',
                'query': "SELECT * FROM calibraciones WHERE equipo_id = ? ORDER BY fecha_calibracion DESC",
            }
        }
    },
    'usuarios': {
        'display_name': 'Usuario / Empleado',
        'table': 'empleados',
        'id_col': 'id',
        'main_field': 'nombre_completo',
        'relations': {
            'activos_asignados': {
                'display_name': 'Activos Tecnológicos Asignados',
                'query': """ 
                    SELECT ei.id, ei.nombre_equipo, ei.marca, ei.modelo, ei.serial, a.fecha_asignacion FROM equipos_individuales ei
                    JOIN asignaciones a ON ei.id = a.asset_id AND a.asset_type = 'equipos_tecnologicos'
                    WHERE a.empleado_id = ? AND a.fecha_devolucion IS NULL
                """,
            },
            'activos_biomedicos_asignados': {
                'display_name': 'Activos Biomédicos Asignados',
                'query': """
                    SELECT eb.id, eb.nombre_equipo, eb.marca, eb.modelo, eb.serie, a.fecha_asignacion FROM equipos_biomedicos eb
                    JOIN asignaciones a ON eb.id = a.asset_id AND a.asset_type = 'equipos_biomedicos'
                    WHERE a.empleado_id = ? AND a.fecha_devolucion IS NULL
                """,
            },
            'solicitudes': {
                'display_name': 'Historial de Solicitudes',
                'query': "SELECT * FROM solicitudes WHERE empleado_id = ? ORDER BY fecha_creacion DESC",
            }
        }
    },
    'sedes': {
        'display_name': 'Sede',
        'table': 'sedes',
        'id_col': 'id',
        'main_field': 'nombre',
        'relations': {
            'empleados_en_sede': {
                'display_name': 'Empleados en esta Sede',
                'query': "SELECT id, nombre_completo, cargo, email FROM empleados WHERE sede_id = ? AND estado = 'activo' ORDER BY nombre_completo",
            },
            'equipos_en_sede': {
                'display_name': 'Equipos en esta Sede',
                'query': "SELECT id, nombre_equipo, marca, modelo, serial FROM equipos_individuales WHERE sede_id = ? ORDER BY nombre_equipo",
            }
        }
    }
}

@asset_profile_bp.route('/<asset_type>/<int:asset_id>')
@login_required
def view_asset_profile(asset_type, asset_id):
    """Muestra la hoja de vida completa de un activo."""
    if asset_type not in ASSET_CONFIG:
        abort(404, "Tipo de activo no válido.")

    config = ASSET_CONFIG[asset_type]
    conn = get_db_connection()

    # 1. Obtener el registro principal del activo
    main_asset = conn.execute(f"SELECT * FROM {config['table']} WHERE {config['id_col']} = ?", (asset_id,)).fetchone()

    if not main_asset:
        abort(404, "Activo no encontrado.")

    # 2. Obtener todos los datos relacionados
    related_data = {}
    if 'relations' in config:
        for key, rel_config in config['relations'].items():
            try:
                related_data[key] = (rel_config['display_name'], conn.execute(rel_config['query'], (asset_id,)).fetchall())
            except sqlite3.OperationalError:
                # Si una tabla relacionada no existe, simplemente no se muestra esa sección
                related_data[key] = (rel_config['display_name'], [])

    conn.close()

    return render_template('asset_profile/view.html', main_asset=main_asset, related_data=related_data, config=config)