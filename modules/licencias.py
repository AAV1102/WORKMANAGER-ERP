from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, Response
import sqlite3
import os
import csv
from datetime import datetime
import io
import pandas as pd

licencias_bp = Blueprint(
    "licencias",
    __name__,
    url_prefix="/licencias",
    template_folder="templates"
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workmanager_erp.db")


def get_db_connection():
    # Si estás usando ruta relativa diferente en tu proyecto, ajusta aquí.
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_licencias_tables(conn):
    """
    Asegura que las tablas necesarias para licencias existan.
    - licencias_office365: detalle por usuario / correo
    - licencias_m365_resumen: resumen por producto (del CSV de Activas)
    """
    cur = conn.cursor()

    # Tabla principal (ya la creas en init_db, pero la dejamos aquí por seguridad)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS licencias_office365 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            tipo_licencia TEXT,
            usuario_asignado TEXT,
            cedula_usuario TEXT,
            sede_id INTEGER,
            estado TEXT DEFAULT 'activa',
            fecha_asignacion TEXT,
            fecha_vencimiento TEXT,
            costo_mensual REAL,
            observaciones TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Resumen de productos (desde "Licencias Office 365 Activas.csv")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS licencias_m365_resumen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_producto TEXT NOT NULL,
            total_licencias INTEGER DEFAULT 0,
            licencias_expiradas INTEGER DEFAULT 0,
            licencias_asignadas INTEGER DEFAULT 0,
            mensaje_estado TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()


# ==========================
#   VISTA PRINCIPAL
# ==========================

@licencias_bp.route("/", methods=["GET"])
def dashboard_licencias():
    """
    Dashboard de Licencias Microsoft 365:
    - Resumen por producto
    - Detalle por usuario/correo
    """
    conn = get_db_connection()
    ensure_licencias_tables(conn)
    cur = conn.cursor()

    # Get filters from request
    sede_filter = request.args.get('sede', '')
    search_query = request.args.get('q', '')

    # Resumen por producto
    cur.execute("""
        SELECT nombre_producto,
               total_licencias,
               licencias_expiradas,
               licencias_asignadas,
               (total_licencias - licencias_asignadas) AS licencias_disponibles,
               mensaje_estado
        FROM licencias_m365_resumen
        ORDER BY nombre_producto ASC
    """)
    resumen = cur.fetchall()

    # Detalle por usuario / correo
    query = """
        SELECT l.*,
               e.id as empleado_id,
               e.nombre as empleado_nombre,
               e.apellido as empleado_apellido,
               e.cedula as empleado_cedula,
               e.cargo as empleado_cargo,
               e.departamento as empleado_departamento,
               s.nombre as sede_nombre
        FROM licencias_office365 l
        LEFT JOIN empleados e ON (LOWER(e.correo_office) = LOWER(l.email) OR e.cedula = l.cedula_usuario)
        LEFT JOIN sedes s ON e.sede_id = s.id OR l.sede_id = s.id
    """
    params = []
    conditions = []

    # Corregido: El filtro de sede debe comprobar el ID de la sede en la tabla de licencias
    # o en la tabla de empleados vinculada.
    if sede_filter and sede_filter.isdigit():
        conditions.append("(l.sede_id = ? OR e.sede_id = ?)")
        params.append(sede_filter)
        params.append(sede_filter)

    if search_query:
        like_query = f"%{search_query}%"
        conditions.append("""
            (LOWER(l.usuario_asignado) LIKE LOWER(?) OR
             LOWER(l.email) LIKE LOWER(?) OR
             LOWER(l.estado) LIKE LOWER(?) OR
             LOWER(e.cargo) LIKE LOWER(?) OR
             LOWER(e.departamento) LIKE LOWER(?) OR
             LOWER(s.nombre) LIKE LOWER(?))
        """)
        params.extend([like_query] * 5)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY l.usuario_asignado ASC"

    try:
        cur.execute(query, params)
        detalle = cur.fetchall()
    except sqlite3.OperationalError as e:
        # Fallback si la tabla empleados no existe o hay un error de columna
        current_app.logger.warning(f"Error en la consulta de licencias (fallback activado): {e}")
        # Ejecutamos una consulta más simple sin el JOIN que puede estar fallando
        simple_query = "SELECT * FROM licencias_office365 ORDER BY usuario_asignado ASC"
        cur.execute(simple_query)
        detalle = cur.fetchall()
        flash("Advertencia: No se pudo cruzar la información con la tabla de empleados. Mostrando datos básicos de licencias.", "warning")

    # KPIs
    total_licencias = sum(r["total_licencias"] or 0 for r in resumen) if resumen else 0
    total_asignadas = sum(r["licencias_asignadas"] or 0 for r in resumen) if resumen else len(detalle)
    total_disponibles = total_licencias - total_asignadas if total_licencias else 0
    total_usuarios_con_licencia = len(detalle)

    # Preparar datos para el gráfico de productos
    chart_labels = []
    chart_data = []
    if resumen:
        # Ordenar por cantidad para un mejor visual
        sorted_resumen = sorted(resumen, key=lambda x: x['total_licencias'], reverse=True)
        for item in sorted_resumen:
            chart_labels.append(item['nombre_producto'])
            chart_data.append(item['total_licencias'])

    # Obtener lista de sedes para el dropdown de filtro
    cur.execute("SELECT id, nombre FROM sedes ORDER BY nombre")
    sedes = cur.fetchall()


    conn.close()

    return render_template(
        "licencias.html",
        resumen=resumen,
        detalle=detalle,
        total_licencias=total_licencias,
        total_asignadas=total_asignadas,
        total_disponibles=total_disponibles,
        total_usuarios_con_licencia=total_usuarios_con_licencia,
        sede_filter=sede_filter,
        search_query=search_query,
        chart_labels=chart_labels,
        chart_data=chart_data,
        sedes=sedes # Pasar las sedes a la plantilla
    )


# ==========================
#   IMPORTAR LICENCIAS ACTIVAS (RESUMEN)
# ==========================

@licencias_bp.route("/import/activas", methods=["POST"])
def import_licencias_activas():
    """
    Importa el archivo "Licencias Office 365 Activas.csv".
    Estructura típica:
    Nombre del producto,Total de licencias,Licencias expiradas,Licencias asignadas,Mensaje de estado
    """
    file = request.files.get("file_activas")
    if not file or file.filename == "":
        flash("Debes seleccionar el archivo 'Licencias Office 365 Activas.csv'.", "danger")
        return redirect(url_for("licencias.dashboard_licencias"))

    # Guardar temporalmente
    upload_dir = os.path.join(current_app.root_path, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    file.save(filepath)

    conn = get_db_connection()
    ensure_licencias_tables(conn)
    cur = conn.cursor()

    try:
        with open(filepath, "r", encoding="latin1", newline="") as f:
            reader = csv.reader(f, delimiter=",")
            rows = list(reader)

        if len(rows) < 2:
            flash("El archivo de licencias activas no tiene filas suficientes.", "danger")
            return redirect(url_for("licencias.dashboard_licencias"))

        header = [h.strip().lower() for h in rows[0]]

        def idx(col_name):
            for i, h in enumerate(header):
                if col_name in h:
                    return i
            return None

        idx_prod = idx("nombre del producto") or idx("product") or 0
        idx_total = idx("total de licencias") or idx("total licenses")
        idx_expiradas = idx("licencias expiradas") or idx("expired")
        idx_asignadas = idx("licencias asignadas") or idx("assigned")
        idx_msg = idx("mensaje de estado") or idx("status")

        # Limpiamos tabla para recargar todo el resumen
        cur.execute("DELETE FROM licencias_m365_resumen")

        for row in rows[1:]:
            if not any(row):
                continue

            nombre_producto = row[idx_prod].strip() if idx_prod is not None and idx_prod < len(row) else ""
            if not nombre_producto:
                continue

            def to_int_safe(index):
                if index is None or index >= len(row):
                    return 0
                val = (row[index] or "").strip()
                try:
                    return int(val)
                except Exception:
                    return 0

            total_lic = to_int_safe(idx_total)
            lic_exp = to_int_safe(idx_expiradas)
            lic_asig = to_int_safe(idx_asignadas)
            mensaje_estado = row[idx_msg].strip() if idx_msg is not None and idx_msg < len(row) else None

            cur.execute("""
                INSERT INTO licencias_m365_resumen (
                    nombre_producto, total_licencias, licencias_expiradas,
                    licencias_asignadas, mensaje_estado
                ) VALUES (?, ?, ?, ?, ?)
            """, (nombre_producto, total_lic, lic_exp, lic_asig, mensaje_estado))

        conn.commit()
        flash("Resumen de licencias activas importado correctamente.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Error al importar licencias activas: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for("licencias.dashboard_licencias"))


# ==========================
#   IMPORTAR LICENCIAS ASIGNADAS (DETALLE)
# ==========================

@licencias_bp.route("/import/asignadas", methods=["POST"])
def import_licencias_asignadas():
    """
    Importa el archivo 'Licencias Office 365 Asignadas.csv'.
    Se basa principalmente en:
    - Display name
    - User principal name (UPN / email)
    - Estado de licencia (si encontramos 'Unlicensed' en la fila, se ignora o se marca inactiva)
    """
    file = request.files.get("file_asignadas")
    if not file or file.filename == "":
        flash("Debes seleccionar el archivo 'Licencias Office 365 Asignadas.csv'.", "danger")
        return redirect(url_for("licencias.dashboard_licencias"))

    upload_dir = os.path.join(current_app.root_path, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, file.filename)
    file.save(filepath)

    conn = get_db_connection()
    ensure_licencias_tables(conn)
    cur = conn.cursor()

    insertados = 0
    actualizados = 0
    sin_correo = 0

    try:
        with open(filepath, "r", encoding="latin1", newline="") as f:
            reader = csv.reader(f, delimiter=",")
            rows = list(reader)

        if len(rows) < 2:
            flash("El archivo de licencias asignadas no tiene filas suficientes.", "danger")
            return redirect(url_for("licencias.dashboard_licencias"))

        header = [h.strip().lower().replace("\ufeff", "") for h in rows[0]]

        def idx_contains(texto):
            for i, h in enumerate(header):
                if texto in h:
                    return i
            return None

        idx_display = idx_contains("display name") or 0
        idx_upn = idx_contains("user principal name") or 2

        for row in rows[1:]:
            if not any(row):
                continue

            display_name = row[idx_display].strip() if idx_display < len(row) else None
            upn = row[idx_upn].strip().lower() if idx_upn < len(row) else None

            if not upn:
                sin_correo += 1
                continue

            # Ver si la fila parece "Unlicensed"
            fila_texto = ",".join(row).lower()
            if "unlicensed" in fila_texto:
                estado = "inactiva"
            else:
                estado = "activa"

            # Sincronizar con empleados: si no existe, crear uno temporal
            cur.execute("SELECT id FROM empleados WHERE LOWER(correo_office) = ?", (upn,))
            empleado_existente = cur.fetchone()
            if not empleado_existente:
                nombre_partes = display_name.split()
                nombre = nombre_partes[0] if nombre_partes else upn.split('@')[0]
                apellido = ' '.join(nombre_partes[1:]) if len(nombre_partes) > 1 else ''
                cur.execute("""
                    INSERT INTO empleados (nombre, apellido, correo_office, estado, nombre_completo)
                    VALUES (?, ?, ?, 'activo', ?)
                """, (nombre, apellido, upn, display_name))
                current_app.logger.info(f"Empleado temporal creado para {upn}")


            # Intentamos buscar algo que parezca fecha en la fila (yyyy-mm-dd)
            fecha_asignacion = None
            for campo in row:
                if isinstance(campo, str) and len(campo) >= 10 and "-" in campo:
                    try:
                        posible = campo.strip()[:10]
                        datetime.strptime(posible, "%Y-%m-%d")
                        fecha_asignacion = posible
                        break
                    except Exception:
                        continue

            # Insertar o actualizar
            cur.execute("SELECT id FROM licencias_office365 WHERE email = ?", (upn,))
            existing = cur.fetchone()

            if existing:
                cur.execute("""
                    UPDATE licencias_office365
                    SET usuario_asignado = ?,
                        estado = ?,
                        fecha_asignacion = COALESCE(?, fecha_asignacion),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (display_name, estado, fecha_asignacion, existing["id"]))
                actualizados += 1
            else:
                cur.execute("""
                    INSERT INTO licencias_office365 (
                        email, tipo_licencia, usuario_asignado,
                        estado, fecha_asignacion
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    upn,
                    "Microsoft 365",  # Tipo genérico; puedes refinarlo luego
                    display_name,
                    estado,
                    fecha_asignacion
                ))
                insertados += 1

        conn.commit()
        if insertados:
            flash(f"Licencias asignadas creadas: {insertados}.", "success")
        if actualizados:
            flash(f"Licencias actualizadas: {actualizados}.", "info")
        if sin_correo:
            flash(f"Filas sin UPN/correo: {sin_correo}.", "warning")

    except Exception as e:
        conn.rollback()
        flash(f"Error al importar licencias asignadas: {e}", "danger")
    finally:
        conn.close()

    return redirect(url_for("licencias.dashboard_licencias"))


# ==========================
#   API SIMPLE (OPCIONAL)
# ==========================

@licencias_bp.route("/api/list", methods=["GET"])
def api_licencias():
    """
    Devuelve el listado de licencias_office365 en JSON.
    Útil si luego quieres conectar con otro módulo o front.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM licencias_office365")
        data = [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()
    return jsonify(data)


@licencias_bp.route("/api/search_users/<query>", methods=["GET"])
def api_search_users(query):
    """
    API para buscar usuarios por nombre, cédula o email.
    Devuelve lista de usuarios para asignación de licencias.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Buscar en tabla empleados (ajusta según tu esquema)
        cur.execute("""
            SELECT id, nombre, apellido, cedula, correo_office, cargo, departamento
            FROM empleados
            WHERE LOWER(nombre) LIKE LOWER(?)
               OR LOWER(apellido) LIKE LOWER(?)
               OR cedula LIKE ?
               OR LOWER(correo_office) LIKE LOWER(?)
            LIMIT 20
        """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
        users = cur.fetchall()
        result = []
        for user in users:
            result.append({
                "id": user["id"],
                "name": f"{user['nombre']} {user['apellido']}",
                "document": user["cedula"],
                "email": user["correo_office"],
                "position": user["cargo"],
                "department": user["departamento"]
            })
    finally:
        conn.close()
    return jsonify(result)


@licencias_bp.route("/api/assign_by_sede", methods=["POST"])
def api_assign_by_sede():
    """
    Asigna licencias por sede específica.
    Recibe: sede_id, tipo_licencia, cantidad
    """
    data = request.get_json()
    sede_id = data.get("sede_id")
    tipo_licencia = data.get("tipo_licencia", "Microsoft 365")
    cantidad = data.get("cantidad", 1)

    if not sede_id:
        return jsonify({"error": "sede_id requerido"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Obtener usuarios de la sede sin licencia asignada
        cur.execute("""
            SELECT e.id, e.nombre, e.apellido, e.cedula, e.correo_office
            FROM empleados e
            LEFT JOIN licencias_office365 l ON LOWER(e.correo_office) = LOWER(l.email)
            WHERE e.sede_id = ? AND l.id IS NULL
            LIMIT ?
        """, (sede_id, cantidad))

        users = cur.fetchall()
        assigned = 0

        for user in users:
            # Crear licencia para el usuario
            cur.execute("""
                INSERT INTO licencias_office365 (
                    email, tipo_licencia, usuario_asignado, cedula_usuario,
                    sede_id, estado, fecha_asignacion
                ) VALUES (?, ?, ?, ?, ?, 'activa', date('now'))
            """, (
                user["correo_office"],
                tipo_licencia,
                f"{user['nombre']} {user['apellido']}",
                user["cedula"],
                sede_id
            ))
            assigned += 1

        conn.commit()
        return jsonify({
            "message": f"Asignadas {assigned} licencias a usuarios de la sede",
            "assigned": assigned
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@licencias_bp.route("/api/assign_user", methods=["POST"])
def api_assign_user():
    """Asigna o actualiza una licencia para un usuario puntual (correo)."""
    data = request.get_json() or {}
    email = data.get("email")
    usuario = data.get("usuario_asignado") or ""
    cedula = data.get("cedula_usuario") or ""
    sede_id = data.get("sede_id")
    estado = data.get("estado") or "activa"
    tipo_licencia = data.get("tipo_licencia") or "Microsoft 365"

    if not email:
        return jsonify({"error": "email requerido"}), 400

    conn = get_db_connection()
    ensure_licencias_tables(conn)
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM licencias_office365 WHERE LOWER(email)=LOWER(?)", (email,))
        row = cur.fetchone()
        if row:
            cur.execute(
                """
                UPDATE licencias_office365
                   SET usuario_asignado=?,
                       cedula_usuario=?,
                       sede_id=?,
                       estado=?,
                       tipo_licencia=?,
                       fecha_asignacion=COALESCE(fecha_asignacion, date('now')),
                       updated_at=CURRENT_TIMESTAMP
                 WHERE id=?
                """,
                (usuario, cedula, sede_id, estado, tipo_licencia, row["id"]),
            )
        else:
            cur.execute(
                """
                INSERT INTO licencias_office365 (
                    email, tipo_licencia, usuario_asignado, cedula_usuario, sede_id, estado, fecha_asignacion
                ) VALUES (?, ?, ?, ?, ?, ?, date('now'))
                """,
                (email, tipo_licencia, usuario, cedula, sede_id, estado),
            )
        conn.commit()
        return jsonify({"message": "Licencia guardada para el usuario", "email": email})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@licencias_bp.route("/api/filter_by_sede/<int:sede_id>", methods=["GET"])
def api_filter_by_sede(sede_id):
    """
    Filtra licencias por sede específica.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT l.*,
                   e.nombre AS empleado_nombre,
                   e.apellido AS empleado_apellido,
                   e.cedula AS empleado_cedula,
                   e.cargo AS empleado_cargo,
                   e.departamento AS empleado_departamento
            FROM licencias_office365 l
            LEFT JOIN empleados e ON LOWER(e.correo_office) = LOWER(l.email)
            WHERE l.sede_id = ?
            ORDER BY l.usuario_asignado ASC
        """, (sede_id,))
        detalle = cur.fetchall()
        result = [dict(row) for row in detalle]
    finally:
        conn.close()
    return jsonify(result)


@licencias_bp.route("/modal/producto/<path:producto>", methods=["GET"])
def licencia_modal_producto(producto):
    """
    Devuelve el contenido HTML para un modal con detalles de un producto.
    Busca usuarios que tengan asignada una licencia que contenga el nombre del producto.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Busca usuarios con ese tipo de licencia
        cur.execute("""
            SELECT l.email, l.usuario_asignado, l.estado, l.fecha_asignacion,
                   e.cargo, e.departamento
            FROM licencias_office365 l
            LEFT JOIN empleados e ON LOWER(e.correo_office) = LOWER(l.email)
            WHERE l.tipo_licencia LIKE ?
            ORDER BY l.usuario_asignado
        """, (f"%{producto}%",))
        usuarios = cur.fetchall()

        # Renderiza un template parcial para el modal
        return render_template("modals/licencia_producto_detalle.html", producto=producto, usuarios=usuarios)

    finally: # Asegura que la conexión se cierre incluso si hay un error
        conn.close()

@licencias_bp.route("/api/detail/<int:licencia_id>", methods=["GET"])
def api_licencia_detail(licencia_id):
    """
    Devuelve los detalles completos de una licencia específica en formato JSON.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT l.*,
                   e.nombre AS empleado_nombre,
                   e.apellido AS empleado_apellido,
                   e.cargo AS empleado_cargo,
                   e.departamento AS empleado_departamento
            FROM licencias_office365 l
            LEFT JOIN empleados e ON LOWER(e.correo_office) = LOWER(l.email)
            WHERE l.id = ?
        """, (licencia_id,))
        licencia = cur.fetchone()
        if licencia:
            return jsonify(dict(licencia))
        return jsonify({"error": "Licencia no encontrada"}), 404
    finally:
        conn.close()


@licencias_bp.route("/exportar/<string:format>", methods=["GET"])
def exportar_licencias(format):
    """
    Exporta los datos de licencias, aplicando los filtros de búsqueda y ordenamiento.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Obtener filtros de la URL
    search_query = request.args.get('q', '')
    sort_by = request.args.get('sort_by', 'usuario_asignado')
    sort_dir = request.args.get('sort_dir', 'asc')

    # Columnas válidas para evitar inyección SQL en ORDER BY
    valid_sort_columns = [
        'usuario_asignado', 'email', 'tipo_licencia', 'estado',
        'fecha_asignacion', 'cedula', 'cargo', 'departamento'
    ]
    if sort_by not in valid_sort_columns:
        sort_by = 'usuario_asignado'
    if sort_dir.lower() not in ['asc', 'desc']:
        sort_dir = 'asc'

    # 2. Construir la consulta con filtros
    query = """
        SELECT
            l.usuario_asignado, l.email, l.tipo_licencia, l.estado,
            l.fecha_asignacion, e.cedula, e.cargo, e.departamento
        FROM licencias_office365 l
        LEFT JOIN empleados e ON (LOWER(e.correo_office) = LOWER(l.email))
    """
    params = []
    if search_query:
        like_query = f"%{search_query}%"
        query += """
            WHERE (LOWER(l.usuario_asignado) LIKE LOWER(?) OR
                   LOWER(l.email) LIKE LOWER(?) OR
                   LOWER(l.estado) LIKE LOWER(?) OR
                   LOWER(e.cargo) LIKE LOWER(?) OR
                   LOWER(e.departamento) LIKE LOWER(?))
        """
        params.extend([like_query] * 5)

    query += f" ORDER BY {sort_by} {sort_dir.upper()}"

    try:
        cur.execute(query, params)
        data = cur.fetchall()
        df = pd.DataFrame([dict(row) for row in data])

        # 3. Generar el archivo de salida
        output = io.BytesIO()
        filename = f"licencias_filtradas_{datetime.now().strftime('%Y%m%d')}"

        if format == 'excel':
            df.to_excel(output, index=False, sheet_name='Licencias')
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            filename += '.xlsx'
        elif format == 'csv':
            df.to_csv(output, index=False, encoding='utf-8-sig')
            mimetype = 'text/csv'
            filename += '.csv'
        else:
            flash("Formato de exportación no válido.", "danger")
            return redirect(url_for('licencias.dashboard_licencias'))

        output.seek(0)

        return Response(
            output,
            mimetype=mimetype,
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )

    except Exception as e:
        flash(f"Error al exportar los datos: {e}", "danger")
        return redirect(url_for('licencias.dashboard_licencias'))
    finally:
        conn.close()

@licencias_bp.route("/limpiar/asignadas", methods=["POST"])
def limpiar_licencias_asignadas():
    """
    Elimina todos los registros de la tabla de licencias asignadas.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM licencias_office365")
        conn.commit()
        flash("Se han eliminado todas las licencias asignadas. Ahora puedes realizar una nueva importación.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al limpiar las licencias asignadas: {e}", "danger")
    finally:
        conn.close()
    
    return redirect(url_for("licencias.dashboard_licencias"))
