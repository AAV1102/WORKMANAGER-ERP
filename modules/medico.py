from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from modules.db_utils import get_db_connection

medico_bp = Blueprint('medico', __name__, template_folder='../templates', static_folder='../static')

@medico_bp.route('/medico')
def medico():
    conn = get_db_connection()
    pacientes = conn.execute('SELECT * FROM pacientes ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('medico.html', pacientes=pacientes)

@medico_bp.route('/paciente/new', methods=['GET', 'POST'])
def new_paciente():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        diagnosis = request.form['diagnosis']
        conn = get_db_connection()
        conn.execute("INSERT INTO pacientes (nombres, apellidos, diagnostico) VALUES (?, ?, ?)", (name, age, diagnosis))
        conn.commit()
        conn.close()
        flash('Paciente added successfully')
        return redirect(url_for('medico.medico'))
    return render_template('new_paciente.html')

@medico_bp.route('/paciente/<int:paciente_id>/edit', methods=['GET', 'POST'])
def edit_paciente(paciente_id):
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        diagnosis = request.form['diagnosis']
        conn.execute("UPDATE pacientes SET nombres=?, apellidos=?, diagnostico=? WHERE id=?", (name, age, diagnosis, paciente_id))
        conn.commit()
        conn.close()
        flash('Paciente updated successfully')
        return redirect(url_for('medico.medico'))
    paciente = conn.execute("SELECT * FROM pacientes WHERE id=?", (paciente_id,)).fetchone()
    conn.close()
    return render_template('edit_paciente.html', paciente=paciente)

@medico_bp.route('/paciente/<int:paciente_id>/delete', methods=['POST'])
def delete_paciente(paciente_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM pacientes WHERE id=?", (paciente_id,))
    conn.commit()
    conn.close()
    flash('Paciente deleted successfully')
    return redirect(url_for('medico.medico'))

@medico_bp.route('/api/pacientes', methods=['GET'])
def api_pacientes():
    conn = get_db_connection()
    pacientes = conn.execute("SELECT * FROM pacientes").fetchall()
    conn.close()
    return jsonify(pacientes)

@medico_bp.route('/medico/nuevo_paciente', methods=['GET', 'POST'])
def nuevo_paciente():
    if request.method == 'POST':
        tipo_documento = request.form['tipo_documento']
        numero_documento = request.form['numero_documento']
        nombres = request.form['nombres']
        apellidos = request.form['apellidos']
        fecha_nacimiento = request.form['fecha_nacimiento']
        genero = request.form['genero']
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        direccion = request.form.get('direccion')
        ciudad = request.form.get('ciudad')
        eps = request.form.get('eps')
        tipo_afiliacion = request.form.get('tipo_afiliacion')

        conn = get_db_connection()
        conn.execute('''INSERT INTO pacientes
                       (tipo_documento, numero_documento, nombres, apellidos, fecha_nacimiento,
                        genero, telefono, email, direccion, ciudad, eps, tipo_afiliacion)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (tipo_documento, numero_documento, nombres, apellidos, fecha_nacimiento,
                     genero, telefono, email, direccion, ciudad, eps, tipo_afiliacion))
        conn.commit()
        conn.close()

        flash('Nuevo paciente creado exitosamente')
        return redirect(url_for('medico.medico'))
    return render_template('medico.html', section='nuevo_paciente')

@medico_bp.route('/medico/citas')
def citas():
    return render_template('medico.html', section='citas')

@medico_bp.route('/medico/historias_clinicas')
def historias_clinicas():
    return render_template('medico.html', section='historias_clinicas')

@medico_bp.route('/medico/examenes')
def examenes():
    return render_template('medico.html', section='examenes')

@medico_bp.route('/medico/medicamentos')
def medicamentos():
    return render_template('medico.html', section='medicamentos')

# Add more CRUD operations as needed
