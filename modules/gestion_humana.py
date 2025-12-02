import os
import sqlite3
from datetime import datetime
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, jsonify
)

gestion_humana_bp = Blueprint(
    "gestion_humana",
    __name__,
    url_prefix="/gestion-humana",
    template_folder="../templates"
)

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "workmanager_erp.db"
)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _ensure_employee_columns(conn)
    _ensure_hr_tables(conn)
    return conn


def _get_sedes(conn):
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, nombre, ciudad FROM sedes ORDER BY nombre")
        return [dict(row) for row in cur.fetchall()]
    except Exception:
        return []


def _ensure_employee_columns(conn):
    """Garantiza columnas extendidas solicitadas."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(empleados)")
    cols = {row[1] for row in cur.fetchall()}
    missing = {
        "fecha_nacimiento": "TEXT",
        "fecha_expedicion": "TEXT",
        "lugar_nacimiento": "TEXT",
        "lugar_expedicion": "TEXT",
        "mes_cumpleanos": "TEXT",
        "tipo_sangre": "TEXT",
        "estado_civil": "TEXT",
        "numero_hijos": "TEXT",
        "genero": "TEXT",
        "empresa": "TEXT",
        "dependencia": "TEXT",
        "nivel_educativo": "TEXT",
        "tarifa": "TEXT",
        "tiempo": "TEXT",
        "afp": "TEXT",
        "eps": "TEXT",
        "cesantias": "TEXT",
        "contrataciones_anteriores": "TEXT",
        "fecha_ultimo_contrato": "TEXT",
        "fecha_proximo_vencimiento": "TEXT",
        "plazo": "TEXT",
        "dias_vencimiento": "TEXT",
        "camisa": "TEXT",
        "pantalon": "TEXT",
        "zapatos": "TEXT",
        "bata": "TEXT",
        "ccf": "TEXT",
        "riesgo": "TEXT",
        "numeral_otro_si": "TEXT",
    }
    for col, typ in missing.items():
        if col not in cols:
            cur.execute(f"ALTER TABLE empleados ADD COLUMN {col} {typ}")
    conn.commit()


def _ensure_hr_tables(conn):
    """Garantiza tablas auxiliares de RRHH para evitar fallos en reportes/solicitudes."""
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hr_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_id INTEGER,
            tipo TEXT,
            descripcion TEXT,
            estado TEXT DEFAULT 'pendiente',
            fecha_solicitud TEXT DEFAULT CURRENT_TIMESTAMP,
            fecha_aprobacion TEXT,
            fecha_rechazo TEXT,
            aprobado_por INTEGER,
            rechazado_por INTEGER,
            motivo_rechazo TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hr_approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            aprobado_por INTEGER,
            decision TEXT,
            comentarios TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hr_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_reporte TEXT,
            periodo TEXT,
            datos TEXT,
            generado_por INTEGER,
            fecha_generacion TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hr_performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empleado_id INTEGER,
            anio INTEGER,
            mes INTEGER,
            performance REAL,
            comentarios TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def _build_employee_payload(form):
    """Construye un diccionario de campos del empleado a partir del formulario."""
    base_fields = {
        "cedula": form.get("cedula", "").strip(),
        "nombre": form.get("nombre", "").strip(),
        "apellido": form.get("apellido", "").strip(),
        "cargo": form.get("cargo", "").strip(),
        "departamento": form.get("departamento", "").strip(),
        "sede_id": form.get("sede_id") or None,
        "fecha_ingreso": form.get("fecha_ingreso", "").strip(),
        "fecha_retiro": form.get("fecha_retiro", "").strip(),
        "razon_social": form.get("razon_social", "").strip(),
        "ciudad": form.get("ciudad", "").strip(),
        "tipo_contrato": form.get("tipo_contrato", "").strip(),
        "codigo_unico_hv_equipo": form.get("codigo_unico_hv_equipo", "").strip(),
        "usuario_windows": form.get("usuario_windows", "").strip(),
        "contrasena_windows": form.get("contrasena_windows", "").strip(),
        "correo_office": form.get("correo_office", "").strip(),
        "usuario_quiron": form.get("usuario_quiron", "").strip(),
        "contrasena_quiron": form.get("contrasena_quiron", "").strip(),
        "observaciones": form.get("observaciones", "").strip(),
        "codigo_biometrico": form.get("codigo_biometrico", "").strip(),
        "estado": form.get("estado", "").strip() or "activo",
        "telefono": form.get("telefono", "").strip(),
        "email": form.get("email", "").strip(),
        "salario": form.get("salario", "").strip(),
        "performance": form.get("performance", "").strip(),
        "fecha_nacimiento": form.get("fecha_nacimiento", "").strip(),
        "nombre_completo": f'{form.get("nombre", "").strip()} {form.get("apellido", "").strip()}',
        "fecha_expedicion": form.get("fecha_expedicion", "").strip(),
        "lugar_nacimiento": form.get("lugar_nacimiento", "").strip(),
        "lugar_expedicion": form.get("lugar_expedicion", "").strip(),
        "mes_cumpleanos": form.get("mes_cumpleanos", "").strip(),
        "tipo_sangre": form.get("tipo_sangre", "").strip(),
        "estado_civil": form.get("estado_civil", "").strip(),
        "numero_hijos": form.get("numero_hijos", "").strip(),
        "genero": form.get("genero", "").strip(),
        "empresa": form.get("empresa", "").strip(),
        "dependencia": form.get("dependencia", "").strip(),
        "nivel_educativo": form.get("nivel_educativo", "").strip(),
        "tarifa": form.get("tarifa", "").strip(),
        "tiempo": form.get("tiempo", "").strip(),
        "afp": form.get("afp", "").strip(),
        "eps": form.get("eps", "").strip(),
        "cesantias": form.get("cesantias", "").strip(),
        "contrataciones_anteriores": form.get("contrataciones_anteriores", "").strip(),
        "fecha_ultimo_contrato": form.get("fecha_ultimo_contrato", "").strip(),
        "fecha_proximo_vencimiento": form.get("fecha_proximo_vencimiento", "").strip(),
        "plazo": form.get("plazo", "").strip(),
        "dias_vencimiento": form.get("dias_vencimiento", "").strip(),
        "camisa": form.get("camisa", "").strip(),
        "pantalon": form.get("pantalon", "").strip(),
        "zapatos": form.get("zapatos", "").strip(),
        "bata": form.get("bata", "").strip(),
        "ccf": form.get("ccf", "").strip(),
        "riesgo": form.get("riesgo", "").strip(),
        "numeral_otro_si": form.get("numeral_otro_si", "").strip(),
    }
    # Apilar extras dentro de observaciones también para trazabilidad rápida
    extras = {k: v for k, v in base_fields.items() if k not in ["observaciones"] and v}
    extra_text = " | ".join([f"{k}={v}" for k, v in extras.items() if k not in ["cedula", "nombre", "apellido"]])
    if extra_text:
        base_fields["observaciones"] = (base_fields.get("observaciones") + "\nExtras: " + extra_text).strip()
    return base_fields


def build_extra_observaciones(extra_fields):
    """
    Convierte el diccionario de campos adicionales en un texto compacto
    para guardarlo en observaciones y no perder trazabilidad.
    """
    return " | ".join([f"{k}={v}" for k, v in extra_fields.items() if v])


# ============= DASHBOARD PRINCIPAL RRHH =============

@gestion_humana_bp.route("/", methods=["GET"])
def dashboard_gestion_humana():
    """
    Dashboard general de Gestión Humana:
      - Lista de empleados
      - Tarjetas de estado
      - Vista rápida de solicitudes y performance (si hay datos)
    """
    search = request.args.get("search", "").strip()
    estado = request.args.get("estado", "").strip()

    conn = get_conn()
    cur = conn.cursor()

    # Empleados
    query = """
        SELECT e.*, s.nombre AS sede_nombre
        FROM empleados e
        LEFT JOIN sedes s ON e.sede_id = s.id
        WHERE 1=1
    """
    params = []
    if search:
        like = f"%{search}%"
        query += """
            AND (
                e.cedula LIKE ?
                OR e.nombre LIKE ?
                OR e.apellido LIKE ?
                OR (e.nombre || ' ' || IFNULL(e.apellido,'')) LIKE ?
                OR e.usuario_windows LIKE ?
                OR e.correo_office LIKE ?
            )
        """
        params += [like, like, like, like, like, like]

    if estado:
        query += " AND e.estado = ? "
        params.append(estado)

    query += " ORDER BY e.nombre, e.apellido "

    cur.execute(query, params)
    empleados = cur.fetchall()

    # Contadores simples
    cur.execute("SELECT COUNT(*) FROM empleados")
    total_empleados = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM empleados WHERE estado = 'activo'")
    total_activos = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM empleados WHERE estado = 'temporal'")
    total_temporales = cur.fetchone()[0] or 0

    cur.execute("SELECT COUNT(*) FROM empleados WHERE estado = 'retirado'")
    total_retirados = cur.fetchone()[0] or 0

    # Solicitudes RRHH (si existen)
    try:
        cur.execute("""
            SELECT COUNT(*) FROM hr_requests
            WHERE estado = 'pendiente'
        """)
        solicitudes_pendientes = cur.fetchone()[0] or 0
    except Exception:
        solicitudes_pendientes = 0

    # Performance simple (promedio)
    try:
        cur.execute("SELECT AVG(performance) FROM empleados WHERE performance IS NOT NULL")
        avg_perf = cur.fetchone()[0]
    except Exception:
        avg_perf = None

    stats = {
        "total_empleados": total_empleados,
        "total_activos": total_activos,
        "total_temporales": total_temporales,
        "total_retirados": total_retirados,
        "solicitudes_pendientes": solicitudes_pendientes,
        "promedio_performance": round(avg_perf, 1) if avg_perf is not None else None
    }

    cur.execute("""
        SELECT hr.*, hr.tipo_solicitud AS tipo_solicitud,
               e.nombre AS empleado_nombre,
               e.apellido AS empleado_apellido,
               e.cargo
        FROM hr_requests hr
        LEFT JOIN empleados e ON hr.empleado_id = e.id
        ORDER BY hr.fecha_solicitud DESC
        LIMIT 5
    """)
    recent_solicitudes = cur.fetchall()

    cur.execute("""
        SELECT hr.*, e.nombre AS generado_por_nombre, e.apellido AS generado_por_apellido
        FROM hr_reports hr
        LEFT JOIN empleados e ON hr.generado_por = e.id
        ORDER BY hr.fecha_generacion DESC
        LIMIT 5
    """)
    recent_reportes = cur.fetchall()

    conn.close()

    return render_template(
        "gestion_humana.html",
        empleados=empleados,
        search=search,
        estado=estado,
        stats=stats,
        recent_solicitudes=recent_solicitudes,
        recent_reportes=recent_reportes
    )


# ============= DETALLE DE EMPLEADO =============

@gestion_humana_bp.route("/empleados/<int:empleado_id>", methods=["GET"])
def detalle_empleado(empleado_id):
    conn = get_conn()
    cur = conn.cursor()

    # Datos de empleado
    cur.execute("""
        SELECT *
        FROM empleados
        WHERE id = ?
        LIMIT 1
    """, (empleado_id,))
    emp = cur.fetchone()

    if not emp:
        conn.close()
        flash("Empleado no encontrado.", "danger")
        return redirect(url_for("gestion_humana.dashboard_gestion_humana"))

    nombre_completo = f"{emp['nombre']} {emp['apellido'] or ''}".strip()

    # Equipos asignados (por código único HV o nombre)
    cur.execute("""
        SELECT ei.*
        FROM equipos_individuales ei
        WHERE ei.asignado_nuevo = ?
           OR ei.codigo_barras_individual = ?
        ORDER BY ei.created_at DESC
    """, (nombre_completo, emp["codigo_unico_hv_equipo"] or ""))

    equipos = cur.fetchall()

    # Licencias Office 365 asignadas
    try:
        cur.execute("""
            SELECT *
            FROM licencias_office365
            WHERE cedula_usuario = ?
               OR usuario_asignado = ?
        """, (emp["cedula"], nombre_completo))
        licencias = cur.fetchall()
    except Exception:
        licencias = []

    # Solicitudes RRHH
    try:
        cur.execute("""
            SELECT hr.*, hr.tipo AS tipo_solicitud
            FROM hr_requests hr
            WHERE empleado_id = ?
            ORDER BY fecha_solicitud DESC
            LIMIT 20
        """, (empleado_id,))
        solicitudes = cur.fetchall()
    except Exception:
        solicitudes = []

    conn.close()

    return render_template(
        "empleado_detalle.html",
        empleado=emp,
        equipos=equipos,
        licencias=licencias,
        solicitudes=solicitudes
    )


@gestion_humana_bp.route("/empleados/<int:empleado_id>/modal")
def empleado_modal(empleado_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM empleados WHERE id = ? LIMIT 1", (empleado_id,))
    empleado = cur.fetchone()

    if not empleado:
        conn.close()
        return "<div class='alert alert-warning'>Empleado no encontrado.</div>"

    nombre_completo = f"{empleado['nombre']} {empleado['apellido'] or ''}".strip()

    cur.execute("""
        SELECT id, codigo_barras_individual, marca, modelo, estado, asignado_nuevo, fecha
        FROM equipos_individuales
        WHERE asignado_nuevo = ?
    """, (nombre_completo,))
    equipos = cur.fetchall()

    try:
        cur.execute("""
            SELECT id, email, tipo_licencia, usuario_asignado, estado, fecha_asignacion
            FROM licencias_office365
            WHERE cedula_usuario = ? OR usuario_asignado = ?
        """, (empleado["cedula"], nombre_completo))
        licencias = cur.fetchall()
    except Exception:
        licencias = []

    conn.close()

    return render_template(
        "modal_empleado_detail.html",
        empleado=empleado,
        equipos=equipos,
        licencias=licencias
    )


# ============= EDICIÓN (RRHH + SISTEMAS) =============

@gestion_humana_bp.route("/empleados/<int:empleado_id>/editar", methods=["GET", "POST"])
def editar_empleado(empleado_id):
    conn = get_conn()
    cur = conn.cursor()

    if request.method == "GET":
        cur.execute("SELECT * FROM empleados WHERE id = ? LIMIT 1", (empleado_id,))
        emp = cur.fetchone()
        conn.close()
        if not emp:
            flash("Empleado no encontrado.", "danger")
            return redirect(url_for("gestion_humana.dashboard_gestion_humana"))
        return render_template("empleado_editar.html", empleado=emp, sedes=_get_sedes(get_conn()))

    # POST: actualizar empleado
    # Campos de Gestión Humana
    cedula = request.form.get("cedula", "").strip()
    nombre = request.form.get("nombre", "").strip()
    # Obtener empleado actual para verificar cambios
    cur.execute("SELECT * FROM empleados WHERE id = ? LIMIT 1", (empleado_id,))
    emp_actual = cur.fetchone()
    if not emp_actual:
        conn.close()
        flash("Empleado no encontrado.", "danger")
        return redirect(url_for("gestion_humana.dashboard_gestion_humana"))

    payload = _build_employee_payload(request.form)

    # Agregar campo rol si viene del formulario
    if 'rol' in request.form:
        payload['rol'] = request.form.get('rol', 'usuario')

    cur.execute("PRAGMA table_info(empleados)")
    cols = {row[1] for row in cur.fetchall()}
    set_clauses = []
    values = []
    for k, v in payload.items():
        if k in cols:
            set_clauses.append(f"{k} = ?")
            values.append(v)
    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    values.append(empleado_id)
    cur.execute(f"UPDATE empleados SET {', '.join(set_clauses)} WHERE id = ?", values)

    # Si el estado cambia a retirado → marcar equipos como "pendiente recogida"
    estado_anterior = emp_actual["estado"]
    estado_nuevo = payload.get("estado")
    if estado_anterior != "retirado" and estado_nuevo == "retirado":
        nombre_completo = f"{emp_actual['nombre']} {emp_actual['apellido'] or ''}".strip()
        cod_hv = emp_actual["codigo_unico_hv_equipo"] or ""

        cur.execute("""
            UPDATE equipos_individuales
            SET estado = 'pendiente recogida',
                disponible = 'No',
                updated_at = CURRENT_TIMESTAMP
            WHERE asignado_nuevo = ?
               OR codigo_barras_individual = ?
        """, (nombre_completo, cod_hv))

    conn.commit()
    conn.close()

    flash("Empleado actualizado correctamente.", "success")
    return redirect(url_for("gestion_humana.detalle_empleado", empleado_id=empleado_id))


# ============= CREAR EMPLEADO (RRHH) =============

@gestion_humana_bp.route("/empleados/nuevo", methods=["GET", "POST"])
def nuevo_empleado():

    if request.method == "GET":
        return render_template("empleado_editar.html", empleado=None, sedes=_get_sedes(get_conn()))

    conn = get_conn()
    cur = conn.cursor()
    payload = _build_employee_payload(request.form)
    payload["estado"] = payload.get("estado") or "activo"

    cur.execute("PRAGMA table_info(empleados)")
    cols = {row[1] for row in cur.fetchall()}
    insert_cols = []
    placeholders = []
    values = []
    for k, v in payload.items():
        if k in cols:
            insert_cols.append(k)
            placeholders.append("?")
            values.append(v)
    insert_cols.extend(["created_at", "updated_at"])
    placeholders.extend(["CURRENT_TIMESTAMP", "CURRENT_TIMESTAMP"])

    cur.execute(
        f"INSERT INTO empleados ({', '.join(insert_cols)}) VALUES ({', '.join(placeholders)})",
        values
    )

    empleado_id = cur.lastrowid
    conn.commit()
    conn.close()

    flash("Empleado creado correctamente.", "success")
    return redirect(url_for("gestion_humana.detalle_empleado", empleado_id=empleado_id))
@gestion_humana_bp.route("/empleados/crear-temporal", methods=["POST"])
def crear_empleado_temporal():
    """
    Crea un empleado temporal cuando desde inventario se intenta asignar
    a alguien que no existe aún. RRHH luego completa el resto.
    """
    data = request.get_json(silent=True) or {}
    q = (data.get("q") or "").strip()

    if not q:
        return jsonify({"success": False, "message": "Dato vacío"}), 400

    conn = get_conn()
    cur = conn.cursor()

    # Si q es todo numérico -> lo tomamos como cédula
    cedula = q if q.isdigit() else ""
    nombre = ""
    apellido = ""

    if not cedula:
        partes = q.split()
        if len(partes) == 1:
            nombre = partes[0]
            apellido = ""
        else:
            nombre = " ".join(partes[:-1])
            apellido = partes[-1]

    # Evitar duplicar si ya existe alguien con esa cédula
    if cedula:
        cur.execute("SELECT id FROM empleados WHERE cedula = ? LIMIT 1", (cedula,))
        existe = cur.fetchone()
        if existe:
            conn.close()
            return jsonify({"success": True, "id": existe["id"]})

    cur.execute("""
        INSERT INTO empleados (
            cedula, nombre, apellido, estado, created_at, updated_at
        ) VALUES (?, ?, ?, 'temporal', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (cedula, nombre, apellido))

    empleado_id = cur.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"success": True, "id": empleado_id})


# ============= SOLICITUDES RRHH =============

@gestion_humana_bp.route("/solicitudes", methods=["GET"])
def solicitudes():
    """
    Lista de solicitudes RRHH
    """
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT hr.*, hr.tipo AS tipo_solicitud,
               e.nombre, e.apellido, e.cargo, e.departamento, e.correo_office, e.cedula
        FROM hr_requests hr
        JOIN empleados e ON hr.empleado_id = e.id
        ORDER BY hr.fecha_solicitud DESC
    """)
    solicitudes = cur.fetchall()

    conn.close()

    return render_template("solicitudes_rrhh.html", solicitudes=solicitudes)


@gestion_humana_bp.route("/solicitudes/<int:solicitud_id>", methods=["GET"])
def ver_solicitud(solicitud_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT hr.*, hr.tipo AS tipo_solicitud,
               e.id AS empleado_id,
               e.nombre AS empleado_nombre,
               e.apellido AS empleado_apellido,
               e.cargo, e.departamento, e.usuario_windows, e.correo_office, e.cedula
        FROM hr_requests hr
        LEFT JOIN empleados e ON hr.empleado_id = e.id
        WHERE hr.id = ?
        LIMIT 1
    """, (solicitud_id,))
    solicitud = cur.fetchone()

    if not solicitud:
        conn.close()
        flash("Solicitud no encontrada.", "danger")
        return redirect(url_for("gestion_humana.solicitudes"))

    empleado_info = None
    if solicitud["empleado_id"]:
        empleado_info = {
            "id": solicitud["empleado_id"],
            "nombre": solicitud["empleado_nombre"],
            "apellido": solicitud["empleado_apellido"],
            "cargo": solicitud["cargo"],
            "departamento": solicitud["departamento"],
            "usuario_windows": solicitud["usuario_windows"],
            "correo_office": solicitud["correo_office"],
            "cedula": solicitud["cedula"],
        }

    cur.execute("""
        SELECT *
        FROM hr_approvals
        WHERE request_id = ?
        ORDER BY created_at DESC
    """, (solicitud_id,))
    aprobaciones = cur.fetchall()

    conn.close()

    return render_template(
        "solicitud_detalle.html",
        solicitud=solicitud,
        empleado=empleado_info,
        aprobaciones=aprobaciones
    )


@gestion_humana_bp.route("/solicitudes/<int:solicitud_id>/aprobar", methods=["POST"])
def aprobar_solicitud(solicitud_id):
    """
    Aprobar una solicitud
    """
    # TODO: Get current user ID from session
    aprobador_id = 1  # Placeholder

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE hr_requests
        SET estado = 'aprobada', fecha_aprobacion = CURRENT_TIMESTAMP, aprobado_por = ?
        WHERE id = ?
    """, (aprobador_id, solicitud_id))

    # Insert into hr_approvals
    cur.execute("""
        INSERT INTO hr_approvals (request_id, aprobado_por, decision, comentarios)
        VALUES (?, ?, 'aprobada', 'Aprobada por RRHH')
    """, (solicitud_id, aprobador_id))

    conn.commit()
    conn.close()

    flash("Solicitud aprobada correctamente.", "success")
    return redirect(url_for("gestion_humana.solicitudes"))


@gestion_humana_bp.route("/solicitudes/<int:solicitud_id>/rechazar", methods=["POST"])
def rechazar_solicitud(solicitud_id):
    """
    Rechazar una solicitud
    """
    motivo = request.form.get("motivo_rechazo", "").strip()
    # TODO: Get current user ID from session
    rechazador_id = 1  # Placeholder

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE hr_requests
        SET estado = 'rechazada', fecha_rechazo = CURRENT_TIMESTAMP, rechazado_por = ?, motivo_rechazo = ?
        WHERE id = ?
    """, (rechazador_id, motivo, solicitud_id))

    # Insert into hr_approvals
    cur.execute("""
        INSERT INTO hr_approvals (request_id, aprobado_por, decision, comentarios)
        VALUES (?, ?, 'rechazada', ?)
    """, (solicitud_id, rechazador_id, motivo))

    conn.commit()
    conn.close()

    flash("Solicitud rechazada.", "success")
    return redirect(url_for("gestion_humana.solicitudes"))


# ============= REPORTES RRHH =============

@gestion_humana_bp.route("/reportes", methods=["GET"])
def reportes():
    """
    Lista de reportes generados
    """
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT hr.*, e.nombre as generado_por_nombre
        FROM hr_reports hr
        LEFT JOIN empleados e ON hr.generado_por = e.id
        ORDER BY hr.fecha_generacion DESC
    """)
    reportes = cur.fetchall()

    conn.close()

    return render_template("reportes_rrhh.html", reportes=reportes)


@gestion_humana_bp.route("/reportes/generar/<tipo>", methods=["POST"])
def generar_reporte(tipo):
    """
    Generar un reporte específico
    """
    conn = get_conn()
    cur = conn.cursor()

    # TODO: Get current user ID
    generado_por = 1  # Placeholder

    if tipo == 'empleados_activos':
        cur.execute("SELECT COUNT(*) as total FROM empleados WHERE estado = 'activo'")
        total = cur.fetchone()['total']
        datos = f"Total empleados activos: {total}"
        periodo = "Actual"

    elif tipo == 'performance':
        cur.execute("SELECT AVG(performance) as avg_perf FROM empleados WHERE performance IS NOT NULL")
        avg_perf = cur.fetchone()['avg_perf'] or 0
        datos = f"Promedio de performance: {avg_perf:.1f}"
        periodo = "Actual"

    elif tipo == 'solicitudes_pendientes':
        cur.execute("SELECT COUNT(*) as total FROM hr_requests WHERE estado = 'pendiente'")
        total = cur.fetchone()['total']
        datos = f"Solicitudes pendientes: {total}"
        periodo = "Actual"

    else:
        datos = "Tipo de reporte no reconocido"
        periodo = "N/A"

    cur.execute("""
        INSERT INTO hr_reports (tipo_reporte, periodo, datos, generado_por, fecha_generacion)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (tipo, periodo, datos, generado_por))

    reporte_id = cur.lastrowid
    conn.commit()
    conn.close()

    flash("Reporte generado exitosamente.", "success")
    return redirect(url_for("gestion_humana.ver_reporte", reporte_id=reporte_id))


@gestion_humana_bp.route("/reportes/<int:reporte_id>", methods=["GET"])
def ver_reporte(reporte_id):
    """
    Ver detalles de un reporte
    """
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM hr_reports WHERE id = ?", (reporte_id,))
    reporte = cur.fetchone()

    conn.close()

    if not reporte:
        flash("Reporte no encontrado.", "danger")
        return redirect(url_for("gestion_humana.reportes"))

    return render_template("ver_reporte.html", reporte=reporte)


# ============= HOJA DE VIDA EMPLEADO =============

@gestion_humana_bp.route("/empleados/<int:empleado_id>/hoja-vida", methods=["GET"])
def hoja_vida_empleado(empleado_id):
    """
    Hoja de vida completa del empleado
    """
    conn = get_conn()
    cur = conn.cursor()

    # Datos del empleado
    cur.execute("SELECT * FROM empleados WHERE id = ?", (empleado_id,))
    empleado = cur.fetchone()

    if not empleado:
        conn.close()
        flash("Empleado no encontrado.", "danger")
        return redirect(url_for("gestion_humana.detalle_empleado", empleado_id=empleado_id))

    # Performance metrics
    cur.execute("""
        SELECT * FROM hr_performance_metrics
        WHERE empleado_id = ?
        ORDER BY anio DESC, mes DESC
    """, (empleado_id,))
    performance = cur.fetchall()

    # Solicitudes RRHH
    cur.execute("""
        SELECT hr.*
        FROM hr_requests hr
        WHERE empleado_id = ?
        ORDER BY fecha_solicitud DESC
    """, (empleado_id,))
    solicitudes = cur.fetchall()

    # Historial de equipos asignados
    cur.execute("""
        SELECT ei.*, 'individual' as tipo
        FROM equipos_individuales ei
        WHERE ei.asignado_nuevo = ? OR ei.codigo_barras_individual = ?
        UNION
        SELECT ea.*, 'agrupado' as tipo
        FROM equipos_agrupados ea
        WHERE ea.asignado_actual = ?
        ORDER BY created_at DESC
    """, (f"{empleado['nombre']} {empleado['apellido'] or ''}".strip(), empleado["codigo_unico_hv_equipo"] or "", f"{empleado['nombre']} {empleado['apellido'] or ''}".strip()))
    equipos = cur.fetchall()

    conn.close()

    return render_template(
        "hoja_vida_empleado.html",
        empleado=empleado,
        performance=performance,
        solicitudes=solicitudes,
        equipos=equipos
    )


@gestion_humana_bp.route("/api/search")
def api_search_empleados():
    """
    API para buscar empleados con filtros avanzados
    """
    query = request.args.get('q', '').strip()
    estado = request.args.get('estado', '').strip()
    cargo = request.args.get('cargo', '').strip()
    sede = request.args.get('sede', '').strip()

    conn = get_conn()
    cur = conn.cursor()

    try:
        sql = """
            SELECT e.*, s.nombre as sede_nombre
            FROM empleados e
            LEFT JOIN sedes s ON e.sede_id = s.id
            WHERE 1=1
        """
        params = []

        if query:
            like_query = f"%{query}%"
            sql += """
                AND (
                    e.cedula LIKE ?
                    OR e.nombre LIKE ?
                    OR e.apellido LIKE ?
                    OR (e.nombre || ' ' || COALESCE(e.apellido, '')) LIKE ?
                    OR e.usuario_windows LIKE ?
                    OR e.correo_office LIKE ?
                    OR e.cargo LIKE ?
                    OR e.ciudad LIKE ?
                )
            """
            params.extend([like_query] * 8)

        if estado:
            sql += " AND e.estado = ?"
            params.append(estado)

        if cargo:
            sql += " AND e.cargo LIKE ?"
            params.append(f"%{cargo}%")

        if sede:
            sql += " AND (s.nombre LIKE ? OR e.sede_id = ?)"
            params.extend([f"%{sede}%", sede])

        sql += " ORDER BY e.nombre, e.apellido LIMIT 100"

        cur.execute(sql, params)
        empleados = cur.fetchall()

        result = []
        for emp in empleados:
            result.append({
                "id": emp["id"],
                "cedula": emp["cedula"],
                "nombre": emp["nombre"],
                "apellido": emp["apellido"],
                "cargo": emp["cargo"],
                "departamento": emp["departamento"],
                "ciudad": emp["ciudad"],
                "sede_id": emp["sede_id"],
                "sede_nombre": emp["sede_nombre"],
                "usuario_windows": emp["usuario_windows"],
                "usuario_quiron": emp["usuario_quiron"],
                "correo_office": emp["correo_office"],
                "codigo_biometrico": emp["codigo_biometrico"],
                "codigo_unico_hv_equipo": emp["codigo_unico_hv_equipo"],
                "estado": emp["estado"],
                "fecha_ingreso": emp["fecha_ingreso"],
                "razon_social": emp["razon_social"]
            })

        return jsonify(result)
    finally:
        conn.close()
