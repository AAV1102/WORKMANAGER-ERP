from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from modules.db_utils import get_db_connection

biomedica_bp = Blueprint('biomedica', __name__, template_folder='../templates', static_folder='../static')

@biomedica_bp.route('/biomedica')
def biomedica():
    conn = get_db_connection()
    equipos = conn.execute('SELECT * FROM equipos_biomedicos ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('biomedica.html', equipos=equipos)

@biomedica_bp.route('/equipo/new', methods=['GET', 'POST'])
def new_equipo():
    if request.method == 'POST':
        name = request.form['name']
        model = request.form['model']
        serial = request.form['serial']
        conn = get_db_connection()
        conn.execute("INSERT INTO equipos_biomedicos (nombre_equipo, modelo, serial) VALUES (?, ?, ?)", (name, model, serial))
        conn.commit()
        conn.close()
        flash('Equipo added successfully')
        return redirect(url_for('biomedica.biomedica'))
    return render_template('new_equipo.html')

@biomedica_bp.route('/equipo/<int:equipo_id>/edit', methods=['GET', 'POST'])
def edit_equipo(equipo_id):
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        model = request.form['model']
        serial = request.form['serial']
        conn.execute("UPDATE equipos_biomedicos SET nombre_equipo=?, modelo=?, serial=? WHERE id=?", (name, model, serial, equipo_id))
        conn.commit()
        conn.close()
        flash('Equipo updated successfully')
        return redirect(url_for('biomedica.biomedica'))
    equipo = conn.execute("SELECT * FROM equipos_biomedicos WHERE id=?", (equipo_id,)).fetchone()
    conn.close()
    return render_template('edit_equipo.html', equipo=equipo)

@biomedica_bp.route('/equipo/<int:equipo_id>/delete', methods=['POST'])
def delete_equipo(equipo_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM equipos_biomedicos WHERE id=?", (equipo_id,))
    conn.commit()
    conn.close()
    flash('Equipo deleted successfully')
    return redirect(url_for('biomedica.biomedica'))

@biomedica_bp.route('/api/equipos', methods=['GET'])
def api_equipos():
    conn = get_db_connection()
    equipos = conn.execute("SELECT * FROM equipos_biomedicos").fetchall()
    conn.close()
    return jsonify([dict(row) for row in equipos])

@biomedica_bp.route('/biomedica/nuevo_equipo', methods=['GET', 'POST'])
def nuevo_equipo():
    if request.method == 'POST':
        codigo_activo = request.form['codigo_activo']
        nombre_equipo = request.form['nombre_equipo']
        marca = request.form['marca']
        modelo = request.form['modelo']
        serial = request.form['serial']
        clasificacion_riesgo = request.form['clasificacion_riesgo']
        registro_invima = request.form.get('registro_invima')
        sede_id = request.form['sede_id']
        ubicacion = request.form['ubicacion']
        estado = request.form['estado']
        fecha_compra = request.form.get('fecha_compra')
        valor_compra = request.form.get('valor_compra')
        proveedor = request.form.get('proveedor')
        fecha_ultimo_mantenimiento = request.form.get('fecha_ultimo_mantenimiento')
        fecha_proximo_mantenimiento = request.form.get('fecha_proximo_mantenimiento')
        observaciones = request.form.get('observaciones')

        conn = get_db_connection()
        conn.execute('''INSERT INTO equipos_biomedicos
                       (codigo_activo, nombre_equipo, marca, modelo, serial, clasificacion_riesgo,
                        registro_invima, sede_id, ubicacion, estado, fecha_compra, valor_compra,
                        proveedor, fecha_ultimo_mantenimiento, fecha_proximo_mantenimiento, observaciones)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (codigo_activo, nombre_equipo, marca, modelo, serial, clasificacion_riesgo,
                     registro_invima, sede_id, ubicacion, estado, fecha_compra, valor_compra,
                     proveedor, fecha_ultimo_mantenimiento, fecha_proximo_mantenimiento, observaciones))
        conn.commit()
        conn.close()

        flash('Nuevo equipo biomédico creado exitosamente')
        return redirect(url_for('biomedica.biomedica'))
    return render_template('biomedica.html', section='nuevo_equipo')

@biomedica_bp.route('/biomedica/mantenimiento')
def mantenimiento():
    return render_template('biomedica.html', section='mantenimiento')

@biomedica_bp.route('/biomedica/programacion')
def programacion():
    return render_template('biomedica.html', section='programacion')

@biomedica_bp.route('/biomedica/calibraciones')
def calibraciones():
    return render_template('biomedica.html', section='calibraciones')

@biomedica_bp.route('/biomedica/certificaciones')
def certificaciones():
    return render_template('biomedica.html', section='certificaciones')

# Add more CRUD operations as needed
