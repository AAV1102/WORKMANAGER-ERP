from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, EmailField, DecimalField, DateField, PasswordField
from wtforms.validators import DataRequired, Email, Length, Optional
from modules.db_utils import get_db_connection

user_bp = Blueprint('user', __name__, url_prefix='/users', template_folder='../templates')

class UserForm(FlaskForm):
    """Formulario para crear y editar usuarios/empleados."""
    nombre = StringField('Nombre', validators=[DataRequired(), Length(min=2, max=50)])
    apellido = StringField('Apellido', validators=[DataRequired(), Length(min=2, max=50)])
    cedula = StringField('Cédula', validators=[DataRequired(), Length(min=5, max=20)])
    email = EmailField('Correo Electrónico', validators=[DataRequired(), Email()])
    telefono = StringField('Teléfono', validators=[Optional(), Length(max=20)])
    cargo = StringField('Cargo', validators=[DataRequired(), Length(max=100)])
    departamento = StringField('Departamento', validators=[Optional(), Length(max=100)])
    salario = DecimalField('Salario', default=0, validators=[Optional()], places=2)
    fecha_ingreso = DateField('Fecha de Ingreso', validators=[Optional()], format='%Y-%m-%d')
    performance = DecimalField('Performance', default=0, validators=[Optional()], places=2)
    sede_id = SelectField('Sede', coerce=int, validators=[DataRequired(message="Debe seleccionar una sede.")])
    password = PasswordField('Contraseña (para nuevo usuario)', validators=[Optional(), Length(min=6)])
    rol = SelectField('Rol', choices=[('usuario', 'Usuario'), ('admin', 'Admin'), ('demo', 'Demo')], default='usuario', validators=[DataRequired()])
    estado = SelectField('Estado', choices=[('activo', 'Activo'), ('inactivo', 'Inactivo')], default='activo', validators=[DataRequired()])
    submit = SubmitField('Guardar Empleado')

@user_bp.route('/')
@login_required
def users():
    """Pagina principal del dashboard de empleados, ahora carga datos dinamicamente."""
    search_nombre = request.args.get('nombre', '').strip()
    search_cedula = request.args.get('cedula', '').strip()
    filter_estado = request.args.get('estado', '').strip()
    filter_departamento = request.args.get('departamento', '').strip()

    conn = get_db_connection()
    try:
        total = conn.execute("SELECT COUNT(id) FROM empleados").fetchone()[0] or 0
        activos = conn.execute("SELECT COUNT(id) FROM empleados WHERE estado = 'activo'").fetchone()[0] or 0
        sedes = conn.execute("SELECT id, nombre FROM sedes ORDER BY nombre").fetchall()

        query = "SELECT * FROM empleados WHERE 1=1"
        params = []
        if search_nombre:
            query += " AND (nombre LIKE ? OR apellido LIKE ?)"
            like = f"%{search_nombre}%"
            params.extend([like, like])
        if search_cedula:
            query += " AND cedula LIKE ?"
            params.append(f"%{search_cedula}%")
        if filter_estado:
            query += " AND estado = ?"
            params.append(filter_estado)
        if filter_departamento:
            query += " AND departamento = ?"
            params.append(filter_departamento)

        query += " ORDER BY nombre"
        users_rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()

    return render_template(
        'users.html',
        total=total,
        activos=activos,
        sedes=sedes,
        users=users_rows,
        search_nombre=search_nombre,
        search_cedula=search_cedula,
        filter_estado=filter_estado,
        filter_departamento=filter_departamento,
    )

@user_bp.route('/dashboard')
@login_required
def users_dashboard():
    """Alias para mantener compatibilidad con /users/dashboard."""
    return redirect(url_for('user.users'))

@user_bp.route('/api/dashboard')
@login_required
def api_dashboard():
    """API que provee todos los datos para el dashboard de empleados."""
    conn = get_db_connection()
    try:
        # Estadísticas
        total = conn.execute("SELECT COUNT(id) FROM empleados").fetchone()[0] or 0
        activos = conn.execute("SELECT COUNT(id) FROM empleados WHERE estado = 'activo'").fetchone()[0] or 0
        
        # Lista de empleados
        query = 'SELECT e.*, s.nombre as sede_nombre FROM empleados e LEFT JOIN sedes s ON e.sede_id = s.id ORDER BY e.nombre'
        empleados = conn.execute(query).fetchall()
        
        return jsonify({
            "stats": {
                "total": total,
                "activos": activos,
            },
            "empleados": [dict(e) for e in empleados]
        })
    finally:
        conn.close()

@user_bp.route('/<int:user_id>/profile')
@login_required
def user_profile(user_id):
    """Muestra el perfil unificado de un empleado."""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM empleados WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if not user:
        flash('Empleado no encontrado.', 'danger')
        return redirect(url_for('user.users'))
    return render_template('user_profile.html', user=user)

@user_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_user():
    form = UserForm()
    # Llenamos dinámicamente las opciones del SelectField de sedes
    conn = get_db_connection()
    sedes = conn.execute('SELECT id, nombre FROM sedes ORDER BY nombre').fetchall()
    conn.close()
    form.sede_id.choices = [(s['id'], s['nombre']) for s in sedes]

    if form.validate_on_submit():
        # El formulario es válido, procedemos a guardar los datos
        conn = get_db_connection()
        try:
            conn.execute('''INSERT INTO empleados
                           (cedula, nombre, apellido, cargo, departamento, telefono, email, salario, fecha_ingreso, estado, sede_id, performance)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (form.cedula.data, form.nombre.data, form.apellido.data, 
                         form.cargo.data, form.departamento.data, form.telefono.data,
                         form.email.data, form.salario.data, form.fecha_ingreso.data, 
                         'activo', form.sede_id.data))
            conn.commit()
            flash('Empleado creado exitosamente.', 'success')
            return redirect(url_for('user.users'))
        except sqlite3.IntegrityError:
            flash('Error: La cédula o el correo electrónico ya existen en la base de datos.', 'danger')
        except Exception as e:
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
        finally:
            conn.close()

    # Si el método es GET o la validación falla, se renderiza el formulario.
    # WTForms se encargará de mostrar los errores.
    return render_template('new_user.html', form=form)

@user_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Muestra el perfil unificado de un empleado."""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM empleados WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if not user:
        flash('Empleado no encontrado.', 'danger')
        return redirect(url_for('user.users'))
    return render_template('user_profile.html', user=user)

@user_bp.route('/api/<int:user_id>/assets')
@login_required
def get_user_assets(user_id):
    """API para obtener los activos asignados a un usuario."""
    conn = get_db_connection()
    # Equipos de inventario 
    equipos = conn.execute('SELECT id, marca, modelo, serial, tecnologia FROM equipos_individuales WHERE usuario_asignado_id = ?', (user_id,)).fetchall()
    # Licencias
    user_cedula = conn.execute('SELECT cedula FROM empleados WHERE id = ?', (user_id,)).fetchone()
    licencias = []
    if user_cedula:
        licencias = conn.execute('SELECT tipo_licencia, email FROM licencias_office365 WHERE cedula_usuario = ?', (user_cedula['cedula'],)).fetchall()
    conn.close()
    return jsonify({
        "equipos": [dict(e) for e in equipos],
        "licencias": [dict(l) for l in licencias]
    })

@user_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM empleados WHERE id=?', (user_id,))
    conn.commit()
    conn.close()
    flash('Usuario eliminado exitosamente')
    return redirect(url_for('user.users'))

@user_bp.route('/api/users', methods=['GET'])
@login_required
def api_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM empleados').fetchall()
    conn.close()
    return jsonify([dict(user) for user in users])

# Add more CRUD operations as needed
