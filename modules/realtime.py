from flask import Blueprint, jsonify
from modules.db_utils import get_db_connection

realtime_bp = Blueprint("realtime", __name__)


def _fetch_one(query, params):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def _fetch_with_join(query, params):
    return _fetch_one(query, params)


@realtime_bp.route("/detail/<module>/<int:item_id>")
def detail(module, item_id):
    handlers = {
        "inventario_individual": lambda: _fetch_one(
            "SELECT * FROM equipos_individuales WHERE id = ?", (item_id,)
        ),
        "inventario_agrupado": lambda: _fetch_one(
            "SELECT * FROM equipos_agrupados WHERE id = ?", (item_id,)
        ),
        "licencia": lambda: _fetch_one(
            "SELECT l.*, e.nombre AS empleado_nombre, e.apellido AS empleado_apellido "
            "FROM licencias_office365 l "
            "LEFT JOIN empleados e ON LOWER(e.correo_office)=LOWER(l.email) "
            "WHERE l.id = ?", (item_id,)
        ),
        "empleado": lambda: _fetch_one(
            "SELECT e.*, s.nombre AS sede_nombre FROM empleados e "
            "LEFT JOIN sedes s ON s.id = e.sede_id WHERE e.id = ?", (item_id,)
        ),
        "ticket": lambda: _fetch_one(
            "SELECT t.*, s.nombre AS sede_nombre FROM tickets t "
            "LEFT JOIN sedes s ON s.id = t.sede_id WHERE t.id = ?", (item_id,)
        ),
        "inventario_administrativo": lambda: _fetch_one(
            "SELECT * FROM inventario_administrativo WHERE id = ?", (item_id,)
        ),
        "insumo": lambda: _fetch_one(
            "SELECT * FROM insumos WHERE id = ?", (item_id,)
        ),
        "factura": lambda: _fetch_one(
            "SELECT * FROM facturas WHERE id = ?", (item_id,)
        ),
        "garantia": lambda: _fetch_one(
            "SELECT * FROM equipos_agrupados WHERE id = ?", (item_id,)
        ),
        "alerta": lambda: _fetch_one(
            "SELECT * FROM ai_logs WHERE id = ?", (item_id,)
        ),
        "asignacion": lambda: _fetch_one(
            "SELECT a.*, e.codigo_barras_individual AS codigo_equipo "
            "FROM asignaciones_equipos a "
            "LEFT JOIN equipos_individuales e ON e.id = a.equipo_id "
            "WHERE a.id = ?", (item_id,)
        ),
        "mantenimiento": lambda: _fetch_one(
            "SELECT * FROM mantenimientos WHERE id = ?", (item_id,)
        ),
        "compra": lambda: _fetch_one(
            "SELECT c.*, e.codigo_barras_individual AS codigo_equipo FROM compras_articulos c "
            "LEFT JOIN equipos_individuales e ON e.id = c.equipo_id WHERE c.id = ?", (item_id,)
        ),
        "sede": lambda: _fetch_one(
            "SELECT * FROM sedes WHERE id = ?", (item_id,)
        ),
        "solicitud": lambda: _fetch_one(
            "SELECT * FROM hr_requests WHERE id = ?", (item_id,)
        ),
        "reporte": lambda: _fetch_one(
            "SELECT * FROM hr_reports WHERE id = ?", (item_id,)
        ),
    }

    handler = handlers.get(module)
    if not handler:
        return jsonify({"error": "Modulo no soportado"}), 400

    data = handler()
    if not data:
        return jsonify({"error": "Elemento no encontrado"}), 404

    return jsonify({"module": module, "data": data})
