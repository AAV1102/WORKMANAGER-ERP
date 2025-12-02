from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3

admin_bp = Blueprint('admin', __name__, template_folder='../templates', static_folder='../static')

def get_db_connection():
    conn = sqlite3.connect('workmanager_erp.db')
    conn.row_factory = sqlite3.Row
    return conn

@admin_bp.route('/admin')
def admin():
    # Estadísticas generales del sistema
    conn = get_db_connection()

    # Contar registros en diferentes tablas
    stats = {}
    tables = ['empleados', 'equipos_agrupados', 'equipos_individuales', 'inventario_administrativo',
              'insumos', 'facturas', 'licencias_office365', 'tickets']

    for table in tables:
        try:
            cursor = conn.execute(f'SELECT COUNT(*) as count FROM {table}')
            stats[table] = cursor.fetchone()['count']
        except:
            stats[table] = 0

    conn.close()
    return render_template('admin.html', stats=stats)

# Inventario Administrativo (Muebles)
@admin_bp.route('/admin/inventario_administrativo')
def inventario_administrativo():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM inventario_administrativo ORDER BY descripcion_item').fetchall()
    conn.close()
    return render_template('inventario_administrativo.html', items=items)

@admin_bp.route('/admin/inventario_administrativo/new', methods=['GET', 'POST'])
def new_inventario_administrativo():
    if request.method == 'POST':
        tipo_mueble = request.form['tipo_mueble']
        sede_id = request.form['sede_id']
        codigo_interno = request.form['codigo_interno']
        estado = request.form['estado']
        descripcion_item = request.form['descripcion_item']
        fecha_compra = request.form['fecha_compra']
        asignado_a = request.form.get('asignado_a', '')
        cantidad = request.form.get('cantidad', 1)
        area_recibe = request.form.get('area_recibe', '')
        cargo_recibe = request.form.get('cargo_recibe', '')
        observaciones = request.form.get('observaciones', '')
        creador_registro = request.form.get('creador_registro', '')

        conn = get_db_connection()
        conn.execute('''INSERT INTO inventario_administrativo
                       (tipo_mueble, sede_id, codigo_interno, estado, descripcion_item, fecha_compra,
                        asignado_a, cantidad, area_recibe, cargo_recibe, observaciones, creador_registro)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (tipo_mueble, sede_id, codigo_interno, estado, descripcion_item, fecha_compra,
                     asignado_a, cantidad, area_recibe, cargo_recibe, observaciones, creador_registro))
        conn.commit()
        conn.close()
        flash('Item de inventario administrativo agregado exitosamente')
        return redirect(url_for('admin.inventario_administrativo'))
    return render_template('new_inventario_administrativo.html')

# Insumos
@admin_bp.route('/admin/insumos')
def insumos():
    conn = get_db_connection()
    insumos_list = conn.execute('SELECT * FROM insumos ORDER BY nombre_insumo').fetchall()
    conn.close()
    return render_template('insumos.html', insumos=insumos_list)

@admin_bp.route('/admin/insumos/new', methods=['GET', 'POST'])
def new_insumo():
    if request.method == 'POST':
        nombre_insumo = request.form['nombre_insumo']
        serial_equipo = request.form.get('serial_equipo', '')
        cantidad_total = request.form['cantidad_total']
        cantidad_disponible = request.form['cantidad_disponible']
        ubicacion = request.form.get('ubicacion', '')
        asignado_a = request.form.get('asignado_a', '')
        creador_registro = request.form.get('creador_registro', '')
        estado = request.form['estado']
        observaciones = request.form.get('observaciones', '')

        conn = get_db_connection()
        conn.execute('''INSERT INTO insumos
                       (nombre_insumo, serial_equipo, cantidad_total, cantidad_disponible,
                        ubicacion, asignado_a, creador_registro, estado, observaciones)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (nombre_insumo, serial_equipo, cantidad_total, cantidad_disponible,
                     ubicacion, asignado_a, creador_registro, estado, observaciones))
        conn.commit()
        conn.close()
        flash('Insumo agregado exitosamente')
        return redirect(url_for('admin.insumos'))
    return render_template('new_insumo.html')

# Proveedores
@admin_bp.route('/admin/proveedores')
def proveedores():
    # Por ahora, obtener proveedores de las facturas
    conn = get_db_connection()
    proveedores_list = conn.execute('SELECT DISTINCT nombre_proveedor FROM facturas WHERE nombre_proveedor IS NOT NULL ORDER BY nombre_proveedor').fetchall()
    conn.close()
    return render_template('proveedores.html', proveedores=proveedores_list)

# Facturas
@admin_bp.route('/admin/facturas')
def facturas():
    conn = get_db_connection()
    facturas_list = conn.execute('SELECT * FROM facturas ORDER BY fecha_factura DESC').fetchall()
    conn.close()
    return render_template('facturas.html', facturas=facturas_list)

@admin_bp.route('/admin/facturas/new', methods=['GET', 'POST'])
def new_factura():
    if request.method == 'POST':
        codigo_interno = request.form['codigo_interno']
        numero_factura = request.form['numero_factura']
        tipo_factura = request.form['tipo_factura']
        valor_factura = request.form['valor_factura']
        nombre_proveedor = request.form['nombre_proveedor']
        item = request.form.get('item', '')
        fecha_factura = request.form['fecha_factura']
        autorizado_por = request.form.get('autorizado_por', '')
        documentos_soporte = request.form.get('documentos_soporte', '')
        observaciones = request.form.get('observaciones', '')

        conn = get_db_connection()
        conn.execute('''INSERT INTO facturas
                       (codigo_interno, numero_factura, tipo_factura, valor_factura, nombre_proveedor,
                        item, fecha_factura, autorizado_por, documentos_soporte, observaciones)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (codigo_interno, numero_factura, tipo_factura, valor_factura, nombre_proveedor,
                     item, fecha_factura, autorizado_por, documentos_soporte, observaciones))
        conn.commit()
        conn.close()
        flash('Factura agregada exitosamente')
        return redirect(url_for('admin.facturas'))
    return render_template('new_factura.html')

# Garantías (por ahora usando una vista simple)
@admin_bp.route('/admin/garantias')
def garantias():
    # Obtener equipos con información de garantía
    conn = get_db_connection()
    garantias_list = conn.execute('''
        SELECT e.*, e.fecha_creacion as fecha_compra
        FROM equipos_agrupados e
        ORDER BY e.fecha_creacion DESC
    ''').fetchall()
    conn.close()
    return render_template('garantias.html', garantias=garantias_list)
