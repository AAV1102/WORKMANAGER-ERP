from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length
import sqlite3
from datetime import datetime
from .notifications import create_notification

solicitudes_bp = Blueprint('solicitudes', __name__, url_prefix='/solicitudes', template_folder='../templates')

def get_db_connection():
    conn = sqlite3.connect('workmanager_erp.db')
    conn.row_factory = sqlite3.Row
    return conn

class SolicitudForm(FlaskForm):
    """Formulario para crear y editar solicitudes."""
    tipo_solicitud = SelectField(
        'Tipo de Solicitud',
        choices=[
            ('vacaciones', 'Vacaciones'),
            ('certificado_laboral', 'Certificado Laboral'),
            ('liquidacion', 'Liquidación'),
            ('permiso_no_remunerado', 'Permiso no Remunerado'),
            ('otro', 'Otro')
        ],
        validators=[DataRequired()]
    )
    fecha_inicio = DateField('Fecha de Inicio (si aplica)', validators=[Optional()], format='%Y-%m-%d')
    fecha_fin = DateField('Fecha de Fin (si aplica)', validators=[Optional()], format='%Y-%m-%d')
    descripcion = TextAreaField('Descripción / Motivo', validators=[DataRequired(), Length(min=10, max=500)])
    submit = SubmitField('Enviar Solicitud')

@solicitudes_bp.route('/')
@login_required
def list_solicitudes():
    """Muestra la lista de solicitudes. Los admins ven todas, los usuarios solo las suyas."""
    conn = get_db_connection()
    
    # Asumimos que un rol 'admin' puede ver todo. Ajusta si tu rol se llama diferente.
    is_admin = hasattr(current_user, 'rol') and current_user.rol == 'admin'
    
    query = """
        SELECT s.id, s.tipo_solicitud, s.estado, s.fecha_creacion, e.nombre, e.apellido
        FROM solicitudes s
        JOIN empleados e ON s.empleado_id = e.id
    """
    params = []

    if not is_admin:
        query += " WHERE s.empleado_id = ?"
        params.append(current_user.id)

    query += " ORDER BY s.fecha_creacion DESC"
    
    solicitudes = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('solicitudes/list.html', solicitudes=solicitudes, is_admin=is_admin)

@solicitudes_bp.route('/pendientes')
@login_required
def list_pendientes():
    """Muestra un reporte de todas las solicitudes pendientes (solo para admins)."""
    is_admin = hasattr(current_user, 'rol') and current_user.rol == 'admin'
    if not is_admin:
        flash('Acceso denegado. Esta vista es solo para administradores.', 'danger')
        return redirect(url_for('solicitudes.list_solicitudes'))

    conn = get_db_connection()
    query = """
        SELECT s.id, s.tipo_solicitud, s.fecha_creacion, e.nombre, e.apellido, e.cargo
        FROM solicitudes s
        JOIN empleados e ON s.empleado_id = e.id
        WHERE s.estado = 'pendiente'
        ORDER BY s.fecha_creacion ASC
    """
    solicitudes_pendientes = conn.execute(query).fetchall()
    conn.close()

    return render_template('solicitudes/pendientes.html', solicitudes=solicitudes_pendientes)

@solicitudes_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva_solicitud():
    """Crea una nueva solicitud para el usuario logueado."""
    form = SolicitudForm()
    if form.validate_on_submit():
        conn = get_db_connection()
        try:
            conn.execute("""
                INSERT INTO solicitudes (empleado_id, tipo_solicitud, fecha_inicio, fecha_fin, descripcion, estado)
                VALUES (?, ?, ?, ?, ?, 'pendiente')
            """, (
                current_user.id,
                form.tipo_solicitud.data,
                form.fecha_inicio.data,
                form.fecha_fin.data,
                form.descripcion.data
            ))
            conn.commit()
            flash('Tu solicitud ha sido enviada correctamente.', 'success')
            return redirect(url_for('solicitudes.list_solicitudes'))
        except Exception as e:
            flash(f'Hubo un error al crear la solicitud: {e}', 'danger')
        finally:
            conn.close()
            
    return render_template('solicitudes/new.html', form=form)

@solicitudes_bp.route('/<int:solicitud_id>/gestionar', methods=['GET', 'POST'])
@login_required
def gestionar_solicitud(solicitud_id):
    """Permite a un admin aprobar o rechazar una solicitud."""
    is_admin = hasattr(current_user, 'rol') and current_user.rol == 'admin'
    if not is_admin:
        flash('No tienes permiso para realizar esta acción.', 'danger')
        return redirect(url_for('solicitudes.list_solicitudes'))

    conn = get_db_connection()
    
    if request.method == 'POST':
        # Obtener el empleado_id antes de que la conexión se cierre
        solicitud_previa = conn.execute("SELECT empleado_id FROM solicitudes WHERE id = ?", (solicitud_id,)).fetchone()
        if not solicitud_previa:
            flash('La solicitud que intentas gestionar ya no existe.', 'danger')
            conn.close()
            return redirect(url_for('solicitudes.list_solicitudes'))
        
        empleado_a_notificar_id = solicitud_previa['empleado_id']

        nuevo_estado = request.form.get('estado')
        respuesta = request.form.get('respuesta_admin', '')
        
        if nuevo_estado in ['aprobada', 'rechazada']:
            try:
                conn.execute("""
                    UPDATE solicitudes 
                    SET estado = ?, respuesta_admin = ?, fecha_actualizacion = ?
                    WHERE id = ?
                """, (nuevo_estado, respuesta, datetime.now(), solicitud_id))
                conn.commit()
                flash(f'La solicitud ha sido {nuevo_estado}.', 'success')

                # --- ¡AQUÍ SE CREA LA NOTIFICACIÓN! ---
                mensaje = f"Tu solicitud ha sido {nuevo_estado}."
                url_destino = url_for('solicitudes.gestionar_solicitud', solicitud_id=solicitud_id)
                create_notification(user_id=empleado_a_notificar_id, message=mensaje, url=url_destino)
                # -----------------------------------------

            except Exception as e:
                flash(f'Error al actualizar la solicitud: {e}', 'danger')
            finally:
                conn.close()
            return redirect(url_for('solicitudes.list_solicitudes'))

    solicitud = conn.execute("""
        SELECT s.*, e.nombre, e.apellido, e.cargo, e.departamento
        FROM solicitudes s
        JOIN empleados e ON s.empleado_id = e.id
        WHERE s.id = ?
    """, (solicitud_id,)).fetchone()
    
    conn.close()

    if not solicitud:
        flash('Solicitud no encontrada.', 'danger')
        return redirect(url_for('solicitudes.list_solicitudes'))
        
    return render_template('solicitudes/gestionar.html', solicitud=solicitud)