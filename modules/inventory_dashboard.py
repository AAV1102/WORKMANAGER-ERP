from flask import Blueprint, render_template
from modules.db_utils import get_db_connection
import json

inventory_dashboard_bp = Blueprint(
    "inventory_dashboard", __name__, template_folder="../templates"
)


@inventory_dashboard_bp.route("/dashboard/inventario")
def dashboard():
    """
    Muestra un dashboard con estadísticas del inventario.
    """
    conn = get_db_connection()
    try:
        total_equipos = conn.execute(
            "SELECT COUNT(id) FROM equipos_individuales"
        ).fetchone()[0]

        equipos_por_estado = conn.execute(
            "SELECT estado, COUNT(id) as total FROM equipos_individuales GROUP BY estado"
        ).fetchall()

    finally:
        conn.close()

    # Preparar datos para el gráfico
    labels = [row["estado"] for row in equipos_por_estado]
    data = [row["total"] for row in equipos_por_estado]

    return render_template("inventory_dashboard/dashboard.html", total_equipos=total_equipos,
                           chart_labels=json.dumps(labels), chart_data=json.dumps(data))