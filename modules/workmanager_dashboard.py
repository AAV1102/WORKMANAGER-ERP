import os
import sqlite3
from flask import Blueprint, render_template

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "workmanager_erp.db")

workmanager_dashboard_bp = Blueprint(
    "workmanager_dashboard",
    __name__,
    url_prefix="/workmanager"
)


@workmanager_dashboard_bp.route("/dashboard")
def dashboard():
    """Dashboard principal WorkManager con modulos y accesos directos."""
    stats = _get_stats()
    quick_links = [
        {"nombre": "Inventarios", "icono": "fa-boxes", "url": "inventarios.inventarios"},
        {"nombre": "Inventario Maestro", "icono": "fa-database", "url": "inventario_maestro.inventario_maestro_home"},
        {"nombre": "Licencias", "icono": "fa-key", "url": "licencias.dashboard_licencias"},
        {"nombre": "RRHH", "icono": "fa-users", "url": "gestion_humana.gestion_humana_dashboard"},
        {"nombre": "Mesa de Ayuda", "icono": "fa-headset", "url": "mesa_ayuda.mesa_ayuda"},
        {"nombre": "Infraestructura", "icono": "fa-server", "url": "infraestructura.infraestructura"},
        {"nombre": "Seguridad", "icono": "fa-shield-alt", "url": "seguridad.seguridad"},
        {"nombre": "Importador", "icono": "fa-file-import", "url": "import_inventario_general.form_inventario_general"},
    ]
    return render_template("workmanager_dashboard.html", stats=stats, quick_links=quick_links)


def _get_stats():
    """Obtiene conteos rapidos desde la base."""
    stats = {
        "equipos": 0,
        "agrupados": 0,
        "licencias": 0,
        "empleados": 0,
        "tickets": 0,
        "proveedores": 0,
    }
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM equipos_individuales")
        stats["equipos"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM equipos_agrupados")
        stats["agrupados"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM licencias_office365")
        stats["licencias"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM empleados")
        stats["empleados"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tickets")
        stats["tickets"] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM proveedores")
        stats["proveedores"] = cur.fetchone()[0]
        conn.close()
    except Exception:
        pass
    return stats
