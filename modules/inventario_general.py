import sqlite3
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from modules.db_utils import get_db_connection

inventario_general_bp = Blueprint(
    'inventario_general',
    __name__,
    template_folder='../templates',
    static_folder='../static',
)


def _scalar(cursor, sql, params=None):
    cursor.execute(sql, params or ())
    row = cursor.fetchone()
    return row[0] if row else 0


def _fetch_sedes(cursor):
    cursor.execute(
        "SELECT id, codigo, nombre, ciudad, departamento FROM sedes ORDER BY nombre"
    )
    return [dict(row) for row in cursor.fetchall()]


@inventario_general_bp.route('/inventario_general')
def inventario_general():
    return redirect(url_for('inventario_general.dashboard_inventario'))


@inventario_general_bp.route('/inventario_general/dashboard')
def dashboard_inventario():
    conn = get_db_connection()
    c = conn.cursor()

    total_agrupados = _scalar(c, "SELECT COUNT(*) FROM equipos_agrupados")
    total_individuales = _scalar(c, "SELECT COUNT(*) FROM equipos_individuales")
    total_empleados = _scalar(c, "SELECT COUNT(*) FROM empleados")

    stats = {
        'total_agrupados': total_agrupados,
        'total_individuales': total_individuales,
        'total_empleados': total_empleados,
        'total_equipos': total_agrupados + total_individuales,
        'agrupados_asignados': _scalar(
            c,
            """
            SELECT COUNT(*)
            FROM equipos_agrupados
            WHERE (TRIM(COALESCE(asignado_actual, '')) != ''
                   OR LOWER(COALESCE(estado_general, '')) IN ('asignado', 'activo', 'usado'))
            """,
        ),
        'agrupados_disponibles': _scalar(
            c,
            """
            SELECT COUNT(*)
            FROM equipos_agrupados
            WHERE LOWER(COALESCE(estado_general, '')) IN (
                'disponible', 'en inventario', 'nuevo', 'stock'
            )
            """,
        ),
        'individual_asignados': _scalar(
            c,
            """
            SELECT COUNT(*)
            FROM equipos_individuales
            WHERE (TRIM(COALESCE(asignado_nuevo, '')) != ''
                   OR LOWER(COALESCE(estado, '')) IN ('asignado', 'activo', 'usado'))
            """,
        ),
        'individual_disponibles': _scalar(
            c,
            """
            SELECT COUNT(*)
            FROM equipos_individuales
            WHERE LOWER(COALESCE(estado, '')) NOT IN (
                'asignado', 'activo', 'usado', 'baja', 'dado de baja'
            )
            """,
        ),
    }

    c.execute(
        """
        SELECT ei.id,
               ei.codigo_barras_individual,
               ei.serial,
               ei.marca,
               ei.modelo,
               ei.tecnologia,
               ei.estado,
               ei.asignado_nuevo,
               COALESCE(s.nombre, 'Sin sede definida') AS sede_nombre,
               ei.fecha_llegada
        FROM equipos_individuales ei
        LEFT JOIN sedes s ON s.id = ei.sede_id
        ORDER BY ei.id DESC
        LIMIT 6
        """
    )
    latest_individuales = [dict(row) for row in c.fetchall()]

    c.execute(
        """
        SELECT ea.id,
               ea.codigo_barras_unificado,
               ea.descripcion_general,
               ea.estado_general,
               ea.asignado_actual,
               COALESCE(s.nombre, 'Sin sede definida') AS sede_nombre,
               ea.fecha_creacion
        FROM equipos_agrupados ea
        LEFT JOIN sedes s ON s.id = ea.sede_id
        ORDER BY ea.id DESC
        LIMIT 6
        """
    )
    latest_agrupados = [dict(row) for row in c.fetchall()]

    c.execute(
        """
        SELECT COALESCE(s.nombre, 'Sin sede definida') AS sede,
               COUNT(ei.id) AS total,
               SUM(
                   CASE
                       WHEN LOWER(COALESCE(ei.estado, '')) IN ('asignado', 'activo', 'usado') THEN 1
                       WHEN TRIM(COALESCE(ei.asignado_nuevo, '')) != '' THEN 1
                       ELSE 0
                   END
               ) AS asignados,
               SUM(
                   CASE
                       WHEN LOWER(COALESCE(ei.estado, '')) IN ('baja', 'dado de baja') THEN 0
                       ELSE 1
                   END
               ) AS disponibles
        FROM equipos_individuales ei
        LEFT JOIN sedes s ON s.id = ei.sede_id
        GROUP BY sede
        ORDER BY total DESC
        LIMIT 6
        """
    )
    sedes_summary = [dict(row) for row in c.fetchall()]

    conn.close()

    return render_template(
        'inventario_general.html',
        stats=stats,
        latest_individuales=latest_individuales,
        latest_agrupados=latest_agrupados,
        sedes_summary=sedes_summary,
    )


@inventario_general_bp.route('/inventario_general/nuevo_agrupado', methods=['GET', 'POST'])
def nuevo_agrupado():
    if request.method == 'POST':
        conn = get_db_connection()
        c = conn.cursor()
        try:
            codigo = (request.form.get('codigo_barras_unificado') or '').strip()
            if not codigo:
                codigo = f"AGRU-{int(datetime.now(timezone.utc).timestamp())}"

            sede_id = request.form.get('sede_id') or None
            if sede_id:
                try:
                    sede_id = int(sede_id)
                except ValueError:
                    sede_id = None

            asignado_actual = request.form.get('asignado_actual', '').strip()
            descripcion = request.form.get('descripcion_general', '').strip()
            creador = request.form.get('creador_registro', '').strip()
            documentos = request.form.get('documentos_entrega', '').strip()
            observaciones = request.form.get('observaciones', '').strip()

            c.execute(
                """
                INSERT INTO equipos_agrupados (
                    codigo_barras_unificado,
                    sede_id,
                    asignado_actual,
                    descripcion_general,
                    creador_registro,
                    documentos_entrega,
                    observaciones,
                    estado_general
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'disponible')
                """,
                (
                    codigo,
                    sede_id,
                    asignado_actual or None,
                    descripcion or None,
                    creador or None,
                    documentos or None,
                    observaciones or None,
                ),
            )
            group_id = c.lastrowid

            componentes = request.form.getlist('componentes_codigos[]')
            for componente in componentes:
                cleaned = (componente or '').strip()
                if not cleaned:
                    continue

                c.execute(
                    """
                    SELECT serial, marca, modelo, tecnologia, estado
                    FROM equipos_individuales
                    WHERE codigo_barras_individual = ? OR placa = ?
                    LIMIT 1
                    """,
                    (cleaned, cleaned),
                )
                detalle = c.fetchone()

                tipo = (
                    detalle['tecnologia'] if detalle and detalle['tecnologia'] else 'Componente adicional'
                )
                marca = detalle['marca'] if detalle else None
                modelo = detalle['modelo'] if detalle else None
                serial = detalle['serial'] if detalle else None

                c.execute(
                    """
                    INSERT INTO equipos_componentes (
                        equipo_agrupado_id,
                        codigo_barras_individual,
                        tipo_componente,
                        marca,
                        modelo,
                        serial
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (group_id, cleaned, tipo, marca, modelo, serial),
                )

            conn.commit()
            flash('Paquete agrupado creado y vinculado correctamente.', 'success')
        except sqlite3.IntegrityError:
            conn.rollback()
            flash('El codigo unificado ya existe. Ingresa uno diferente.', 'danger')
        finally:
            conn.close()
        return redirect(url_for('inventario_general.dashboard_inventario'))

    conn = get_db_connection()
    c = conn.cursor()
    sedes = _fetch_sedes(c)
    conn.close()
    return render_template('new_inventario_agrupado.html', sedes=sedes)


@inventario_general_bp.route('/inventario_general/hoja_vida/<tipo>/<int:registro_id>')
def hoja_vida(tipo, registro_id):
    if tipo not in ('individual', 'agrupado'):
        flash('Tipo de equipo no valido para consultar la hoja de vida.', 'warning')
        return redirect(url_for('inventario_general.dashboard_inventario'))

    conn = get_db_connection()
    c = conn.cursor()
    equipo_table = 'equipos_individuales' if tipo == 'individual' else 'equipos_agrupados'
    c.execute(f"SELECT * FROM {equipo_table} WHERE id = ?", (registro_id,))
    equipo = c.fetchone()

    c.execute(
        """
        SELECT *
        FROM hoja_vida_equipos
        WHERE equipo_id = ? AND tipo_equipo = ?
        ORDER BY fecha_accion DESC
        """,
        (registro_id, tipo),
    )
    registros = c.fetchall()
    conn.close()
    return render_template('hoja_vida.html', equipo=equipo, registros=registros, tipo=tipo)


@inventario_general_bp.route('/inventario_general/buscar_empleado')
def buscar_empleado():
    query = (request.args.get('q') or '').strip()
    conn = get_db_connection()
    c = conn.cursor()

    if query:
        like = f'%{query}%'
        c.execute(
            """
            SELECT id, cedula, nombre, apellido, cargo, departamento, correo_office, sede_id
            FROM empleados
            WHERE cedula LIKE ?
               OR nombre LIKE ?
               OR apellido LIKE ?
               OR correo_office LIKE ?
            LIMIT 12
            """,
            (like, like, like, like),
        )
    else:
        c.execute(
            """
            SELECT id, cedula, nombre, apellido, cargo, departamento, correo_office, sede_id
            FROM empleados
            ORDER BY id DESC
            LIMIT 10
            """
        )

    empleados = []
    for row in c.fetchall():
        empleados.append(
            {
                'id': row['id'],
                'cedula': row['cedula'],
                'nombre': row['nombre'],
                'apellido': row['apellido'],
                'cargo': row['cargo'],
                'departamento': row['departamento'],
                'correo_office': row['correo_office'],
                'sede_id': row['sede_id'],
            }
        )

    conn.close()
    return jsonify(empleados)
