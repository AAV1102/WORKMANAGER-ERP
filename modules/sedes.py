from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os

sedes_bp = Blueprint('sedes', __name__, template_folder='../templates', static_folder='../static')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workmanager_erp.db")

@sedes_bp.route('/sedes')
def sedes():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get all sedes with statistics
    c.execute("""
        SELECT s.*,
               COUNT(DISTINCT ea.id) as equipos_agrupados,
               COUNT(DISTINCT ei.id) as equipos_individuales,
               COUNT(DISTINCT e.id) as empleados
        FROM sedes s
        LEFT JOIN equipos_agrupados ea ON s.id = ea.sede_id
        LEFT JOIN equipos_individuales ei ON s.id = ei.sede_id
        LEFT JOIN empleados e ON s.id = e.sede_id
        GROUP BY s.id
        ORDER BY s.nombre
    """)
    sedes_list = c.fetchall()

    # Calculate totals
    total_sedes = len(sedes_list)
    total_equipos_agrupados = sum(int(row['equipos_agrupados']) for row in sedes_list) if sedes_list else 0
    total_equipos_individuales = sum(int(row['equipos_individuales'] or 0) for row in sedes_list) if sedes_list else 0
    total_empleados = sum(int(row['empleados']) for row in sedes_list) if sedes_list else 0

    stats = {
        'total_sedes': total_sedes,
        'total_equipos_agrupados': total_equipos_agrupados,
        'total_equipos_individuales': total_equipos_individuales,
        'total_equipos': total_equipos_agrupados + total_equipos_individuales,
        'total_empleados': total_empleados
    }

    conn.close()
    return render_template('sedes.html', sedes=sedes_list, stats=stats)

@sedes_bp.route('/sede/<int:sede_id>')
def sede_detail(sede_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get sede info
    c.execute("SELECT * FROM sedes WHERE id=?", (sede_id,))
    sede = c.fetchone()

    if not sede:
        flash('Sede no encontrada')
        return redirect(url_for('sedes.sedes'))

    ciudad = sede['ciudad'] or ''
    sede_codigo = (sede['codigo'] or '').strip()
    if not sede_codigo:
        sede_codigo = f"S{str(sede_id).zfill(3)}"
    sede_codigo = sede_codigo.replace(' ', '').upper()
    codigo_agrupado_sede = f"AGR-{sede_codigo}"

    # Inventario agrupado por sede
    c.execute("""
        SELECT id, codigo_barras_unificado, descripcion_general, asignado_actual, estado_general
        FROM equipos_agrupados
        WHERE sede_id = ?
        ORDER BY id DESC
    """, (sede_id,))
    inventario_tecnologico_agrupado = [dict(row) for row in c.fetchall()]

    # Inventario individual por sede
    c.execute("""
        SELECT id, codigo_barras_individual, serial, marca, modelo, estado
        FROM equipos_individuales
        WHERE sede_id = ?
        ORDER BY id DESC
    """, (sede_id,))
    inventario_tecnologico_individual = [dict(row) for row in c.fetchall()]

    # Inventario administrativo por sede
    c.execute("""
        SELECT id, tipo_mueble, codigo_interno, descripcion_item, asignado_a, estado
        FROM inventario_administrativo
        WHERE sede_id = ?
        ORDER BY id DESC
    """, (sede_id,))
    inventario_administrativo = [dict(row) for row in c.fetchall()]

    # Insumos filtrados por sede (ubicacion contiene ciudad o sede_id si existiera)
    c.execute("""
        SELECT id, nombre_insumo, serial_equipo, cantidad_total, cantidad_disponible, asignado_a, estado, ubicacion
        FROM insumos
        WHERE (ubicacion IS NOT NULL AND ubicacion LIKE ?)
    """, (f"%{ciudad}%",))
    insumos = [dict(row) for row in c.fetchall()]

    # Biomédica por sede
    c.execute("""
        SELECT id, codigo_activo, nombre_equipo, marca, modelo, estado
        FROM equipos_biomedicos
        WHERE sede_id = ?
        ORDER BY id DESC
    """, (sede_id,))
    biomedica = [dict(row) for row in c.fetchall()]

    # Licencias por sede
    c.execute("""
        SELECT id, email, tipo_licencia, usuario_asignado, estado, fecha_vencimiento
        FROM licencias_office365
        WHERE sede_id = ?
        ORDER BY id DESC
    """, (sede_id,))
    licencias = [dict(row) for row in c.fetchall()]

    # Tickets por sede
    c.execute("""
        SELECT id, numero_ticket, titulo, categoria, prioridad, estado
        FROM tickets
        WHERE sede_id = ?
        ORDER BY created_at DESC
    """, (sede_id,))
    tickets = [dict(row) for row in c.fetchall()]

    # Empleados por sede (incluye conteos de equipos/licencias)
    c.execute("""
        SELECT e.*,
               COALESCE((
                   SELECT COUNT(*) FROM equipos_individuales ei
                   WHERE (TRIM(ei.asignado_nuevo) = TRIM(e.nombre || ' ' || IFNULL(e.apellido, '')))
                      OR (ei.codigo_unificado = e.codigo_unico_hv_equipo)
               ), 0) AS equipos_asignados,
               COALESCE((
                   SELECT COUNT(*) FROM licencias_office365 l
                   WHERE LOWER(l.email) = LOWER(e.correo_office)
                      OR LOWER(l.usuario_asignado) LIKE '%' || LOWER(e.nombre || ' ' || IFNULL(e.apellido,'')) || '%'
               ), 0) AS licencias_asignadas
        FROM empleados e
        WHERE e.sede_id = ?
        ORDER BY e.nombre, e.apellido
    """, (sede_id,))
    empleados = [dict(row) for row in c.fetchall()]

    # Inventario summary (individual) por sede
    c.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN LOWER(COALESCE(estado, '')) IN ('disponible','activo','nuevo','buen estado','bueno') THEN 1 ELSE 0 END) AS disponibles,
            SUM(CASE WHEN LOWER(COALESCE(estado, '')) LIKE 'baja%' THEN 1 ELSE 0 END) AS bajas,
            SUM(CASE WHEN (asignado_nuevo IS NOT NULL AND TRIM(asignado_nuevo) != '') OR LOWER(COALESCE(estado, '')) IN ('asignado','en uso','usado') THEN 1 ELSE 0 END) AS asignados
        FROM equipos_individuales
        WHERE sede_id = ?
    """, (sede_id,))
    row = c.fetchone()
    inventario_summary = dict(row) if row else {"total": 0, "disponibles": 0, "bajas": 0, "asignados": 0}

    # Breakdown por tecnología
    c.execute("""
        SELECT tecnologia, COUNT(*) AS total
        FROM equipos_individuales
        WHERE sede_id = ?
        GROUP BY tecnologia
        ORDER BY total DESC
        LIMIT 15
    """, (sede_id,))
    tecnologia_breakdown = [dict(row) for row in c.fetchall()]

    # Licencias summary
    c.execute("""
        SELECT estado, COUNT(*) AS total
        FROM licencias_office365
        WHERE sede_id = ?
        GROUP BY estado
    """, (sede_id,))
    licencias_summary = {row['estado'] or 'sin_estado': row['total'] for row in c.fetchall()}

    # Tickets summary
    c.execute("""
        SELECT estado, COUNT(*) AS total
        FROM tickets
        WHERE sede_id = ?
        GROUP BY estado
    """, (sede_id,))
    tickets_summary = {row['estado'] or 'sin_estado': row['total'] for row in c.fetchall()}

    # Estado general para plantilla
    sede_stats = {
        "total_equipos_individuales": inventario_summary.get("total", 0) or 0,
        "disponibles": inventario_summary.get("disponibles", 0) or 0,
        "asignados": inventario_summary.get("asignados", 0) or 0,
        "bajas": inventario_summary.get("bajas", 0) or 0,
        "total_licencias": sum(licencias_summary.values()),
        "tickets": sum(tickets_summary.values()),
        "empleados": len(empleados),
    }

    # Crear código agrupado para la sede si no existe
    try:
        c.execute("SELECT id FROM equipos_agrupados WHERE codigo_barras_unificado = ?", (codigo_agrupado_sede,))
        if not c.fetchone():
            c.execute("""
                INSERT INTO equipos_agrupados (
                    codigo_barras_unificado, descripcion_general, sede_id, estado_general, created_at
                ) VALUES (?, ?, ?, 'activo', CURRENT_TIMESTAMP)
            """, (codigo_agrupado_sede, f"Equipo Agrupado - {sede['nombre']}", sede_id))
            conn.commit()
    except Exception as e:
        print(f"Error creando código agrupado para sede: {e}")

    conn.close()

    return render_template(
        'sede_detail.html',
        sede=dict(sede),
        codigo_agrupado_sede=codigo_agrupado_sede,
        inventario_tecnologico_agrupado=inventario_tecnologico_agrupado,
        inventario_tecnologico_individual=inventario_tecnologico_individual,
        inventario_administrativo=inventario_administrativo,
        insumos=insumos,
        biomedica=biomedica,
        licencias=licencias,
        tickets=tickets,
        empleados=empleados,
        sede_stats=sede_stats,
        tecnologia_breakdown=tecnologia_breakdown,
        licencias_summary=licencias_summary,
        tickets_summary=tickets_summary,
    )

@sedes_bp.route('/api/sedes', methods=['GET'])
def api_sedes():
    conn = sqlite3.connect('workmanager_erp.db')
    c = conn.cursor()
    c.execute("SELECT * FROM sedes")
    sedes = c.fetchall()
    conn.close()
    return jsonify([dict(sede) for sede in sedes])
