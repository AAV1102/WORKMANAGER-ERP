from flask import Blueprint, render_template, abort
from flask_login import login_required
import sqlite3

asset_profile_bp = Blueprint(
    "asset_profile",
    __name__,
    url_prefix="/asset_profile",
    template_folder="../templates",
)


def get_db_connection():
    conn = sqlite3.connect("workmanager_erp.db")
    conn.row_factory = sqlite3.Row
    return conn


# --- CONFIGURACION CENTRAL DE ACTIVOS ---
# Esta configuracion define como buscar y relacionar datos para cada tipo de activo.
ASSET_CONFIG = {
    "equipos_tecnologicos": {
        "display_name": "Equipo Tecnologico",
        "table": "equipos_individuales",
        "id_col": "id",
        "main_field": "nombre_equipo",
        "relations": {
            "mantenimientos": {
                "display_name": "Historial de Mantenimiento",
                "query": "SELECT * FROM mantenimientos WHERE equipo_id = ? ORDER BY fecha_mantenimiento DESC",
            },
            "asignaciones": {
                "display_name": "Historial de Asignaciones",
                "query": """
                    SELECT a.*, e.nombre_completo as empleado FROM asignaciones a 
                    LEFT JOIN empleados e ON a.empleado_id = e.id
                    WHERE a.asset_type = 'equipos_tecnologicos' AND a.asset_id = ? ORDER BY a.fecha_asignacion DESC
                """,
            },
            "tickets": {
                "display_name": "Tickets de Soporte",
                "query": "SELECT * FROM tickets WHERE asset_serial = (SELECT serial FROM equipos_individuales WHERE id = ?) ORDER BY fecha_creacion DESC",
            },
        },
    },
    "equipos_biomedicos": {
        "display_name": "Equipo Biomedico",
        "table": "equipos_biomedicos",
        "id_col": "id",
        "main_field": "nombre_equipo",
        "relations": {
            "mantenimientos": {
                "display_name": "Historial de Mantenimiento Biomedico",
                "query": "SELECT * FROM mantenimientos_biomedicos WHERE equipo_id = ? ORDER BY fecha_mantenimiento DESC",
            },
            "asignaciones": {
                "display_name": "Historial de Asignaciones",
                "query": "SELECT a.*, e.nombre_completo as empleado FROM asignaciones a LEFT JOIN empleados e ON a.empleado_id = e.id WHERE a.asset_type = 'equipos_biomedicos' AND a.asset_id = ? ORDER BY a.fecha_asignacion DESC",
            },
            "calibraciones": {
                "display_name": "Registros de Calibracion",
                "query": "SELECT * FROM calibraciones WHERE equipo_id = ? ORDER BY fecha_calibracion DESC",
            },
        },
    },
    "agrupado": {
        "display_name": "Equipo Agrupado",
        "table": "equipos_agrupados",
        "id_col": "id",
        "main_field": "descripcion_general",
        "relations": {
            "componentes": {
                "display_name": "Componentes del Paquete",
                "query": "SELECT * FROM equipos_componentes WHERE equipo_agrupado_id = ? ORDER BY id DESC",
            },
            "asignaciones": {
                "display_name": "Historial de Asignaciones",
                "query": """
                    SELECT a.* FROM asignaciones WHERE asset_type = 'agrupado' AND asset_id = ? ORDER BY fecha_asignacion DESC
                """,
            },
            "trazabilidad": {
                "display_name": "Trazabilidad / Hoja de Vida",
                "query": "SELECT * FROM hoja_vida_equipos WHERE tipo_equipo = 'agrupado' AND equipo_id = ? ORDER BY fecha_accion DESC",
            },
        },
    },
    "usuarios": {
        "display_name": "Usuario / Empleado",
        "table": "empleados",
        "id_col": "id",
        "main_field": "nombre_completo",
        "relations": {
            "activos_asignados": {
                "display_name": "Activos Tecnologicos Asignados",
                "query": """
                    SELECT ei.id, ei.nombre_equipo, ei.marca, ei.modelo, ei.serial, a.fecha_asignacion FROM equipos_individuales ei
                    JOIN asignaciones a ON ei.id = a.asset_id AND a.asset_type = 'equipos_tecnologicos'
                    WHERE a.empleado_id = ? AND a.fecha_devolucion IS NULL
                """,
            },
            "activos_biomedicos_asignados": {
                "display_name": "Activos Biomedicos Asignados",
                "query": """
                    SELECT eb.id, eb.nombre_equipo, eb.marca, eb.modelo, eb.serie, a.fecha_asignacion FROM equipos_biomedicos eb
                    JOIN asignaciones a ON eb.id = a.asset_id AND a.asset_type = 'equipos_biomedicos'
                    WHERE a.empleado_id = ? AND a.fecha_devolucion IS NULL
                """,
            },
            "solicitudes": {
                "display_name": "Historial de Solicitudes",
                "query": "SELECT * FROM solicitudes WHERE empleado_id = ? ORDER BY fecha_creacion DESC",
            },
        },
    },
    "sedes": {
        "display_name": "Sede",
        "table": "sedes",
        "id_col": "id",
        "main_field": "nombre",
        "relations": {
            "empleados_en_sede": {
                "display_name": "Empleados en esta Sede",
                "query": "SELECT id, nombre_completo, cargo, email FROM empleados WHERE sede_id = ? AND estado = 'activo' ORDER BY nombre_completo",
            },
            "equipos_en_sede": {
                "display_name": "Equipos en esta Sede",
                "query": "SELECT id, nombre_equipo, marca, modelo, serial FROM equipos_individuales WHERE sede_id = ? ORDER BY nombre_equipo",
            },
        },
    },
}


@asset_profile_bp.route("/view/<asset_type>/<int:asset_id>")
@asset_profile_bp.route("/<asset_type>/<int:asset_id>")
@login_required
def view_asset_profile(asset_type, asset_id):
    """Muestra la hoja de vida completa de un activo."""
    if asset_type not in ASSET_CONFIG:
        abort(404, "Tipo de activo no valido.")

    config = ASSET_CONFIG[asset_type]
    conn = get_db_connection()

    # 1. Obtener el registro principal del activo
    main_asset = conn.execute(
        f"SELECT * FROM {config['table']} WHERE {config['id_col']} = ?",
        (asset_id,),
    ).fetchone()

    if not main_asset:
        conn.close()
        abort(404, "Activo no encontrado.")

    # 2. Obtener todos los datos relacionados
    related_data = {}
    if "relations" in config:
        for key, rel_config in config["relations"].items():
            try:
                related_data[key] = (
                    rel_config["display_name"],
                    conn.execute(rel_config["query"], (asset_id,)).fetchall(),
                )
            except sqlite3.OperationalError:
                # Si una tabla relacionada no existe, simplemente no se muestra esa seccion
                related_data[key] = (rel_config["display_name"], [])

    conn.close()

    return render_template(
        "asset_profile/view.html",
        main_asset=main_asset,
        related_data=related_data,
        config=config,
    )
