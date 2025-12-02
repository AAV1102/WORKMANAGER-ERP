from flask import Blueprint, render_template, request
from modules.db_utils import get_db_connection
import math

visualizador_bp = Blueprint(
    "visualizador_inventario", __name__, template_folder="../templates"
)

def get_pagination_range(current_page, total_pages, window=2):
    """Genera una lista de números de página para la paginación."""
    if total_pages <= (window * 2) + 1:
        return list(range(1, total_pages + 1))

    pages = []
    # Páginas alrededor de la actual
    start = max(2, current_page - window)
    end = min(total_pages - 1, current_page + window)

    pages.append(1)
    if start > 2:
        pages.append(None)  # Ellipsis
    pages.extend(range(start, end + 1))
    if end < total_pages - 1:
        pages.append(None)  # Ellipsis
    pages.append(total_pages)
    return pages

@visualizador_bp.route("/inventario/individual")
def listar_equipos_individuales():
    """
    Muestra una lista paginada de todos los equipos en la tabla equipos_individuales.
    """
    conn = get_db_connection()
    search_query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 15  # Número de equipos por página
    offset = (page - 1) * per_page
    
    # Columnas que queremos mostrar en la tabla
    columnas_visibles = [
        "id", "codigo_barras_individual", "tecnologia", "marca", "modelo", 
        "serial", "estado", "asignado_nuevo", "ciudad"
    ]
    columnas_str = ", ".join(columnas_visibles)
    
    params = []
    count_params = []
    
    # Construcción de la cláusula WHERE para la búsqueda
    where_clause = ""
    if search_query:
        where_clause = " WHERE serial LIKE ? OR modelo LIKE ? OR marca LIKE ?"
        search_term = f"%{search_query}%"
        params.extend([search_term, search_term, search_term])
        count_params.extend([search_term, search_term, search_term])

    # Consulta para obtener el total de registros (para la paginación)
    count_query = f"SELECT COUNT(id) FROM equipos_individuales{where_clause}"
    
    # Consulta para obtener los registros de la página actual
    data_query = f"SELECT {columnas_str} FROM equipos_individuales{where_clause} ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    total_equipos = 0
    equipos = []
    try:
        total_equipos = conn.execute(count_query, count_params).fetchone()[0]
        equipos = conn.execute(data_query, params).fetchall()
    except Exception as e:
        print(f"Error al consultar la base de datos: {e}")
        equipos = [] # Devolver una lista vacía en caso de error
    finally:
        conn.close()

    total_pages = math.ceil(total_equipos / per_page)
    pagination_range = get_pagination_range(page, total_pages)

    return render_template(
        "visualizador/lista_equipos.html", # Asumiendo que el template está en la carpeta correcta
        equipos=equipos,
        columnas=columnas_visibles,
        titulo="Inventario de Equipos Individuales",
        search_query=search_query,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        total_equipos=total_equipos,
        pagination_range=pagination_range
    )