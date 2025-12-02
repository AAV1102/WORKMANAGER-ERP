from email.message import EmailMessage
import smtplib

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from flask_login import login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from modules.db_utils import (
    get_db_connection,
    load_active_db_path,
    save_active_db_path,
    list_available_dbs,
)
from modules.credentials_config import DEFAULT_ADMIN, DEMO_USER, mask_password

auth_bp = Blueprint('auth', __name__, template_folder='../templates', static_folder='../static')


def send_credentials_email(target_email, nombre, plain_password, active_db):
    config = current_app.config
    host = config.get('MAIL_SERVER', 'smtp.gmail.com')
    port = int(config.get('MAIL_PORT', 587))
    use_tls = str(config.get('MAIL_USE_TLS', True)).lower() == 'true'
    username = config.get('MAIL_USERNAME')
    password = config.get('MAIL_PASSWORD')

    if not target_email:
        return False, 'No se especificó destinatario.'
    if not username or not password:
        return False, 'Configura MAIL_USERNAME y MAIL_PASSWORD para enviar correos.'

    try:
        msg = EmailMessage()
        msg['Subject'] = 'Credenciales de acceso WorkManager ERP'
        msg['From'] = username
        msg['To'] = target_email
        nombre_line = nombre or target_email
        msg.set_content(
            f"Hola {nombre_line},\n\n"
            f"Aquí están tus credenciales de acceso:\n"
            f"- Usuario: {target_email}\n"
            f"- Contraseña: {plain_password}\n"
            f"- Base de datos activa: {active_db}\n\n"
            "Por seguridad cambia la contraseña al iniciar sesión."
        )

        with smtplib.SMTP(host, port) as smtp:
            if use_tls:
                smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(msg)
        return True, 'Credenciales enviadas por correo.'
    except Exception as exc:
        return False, f'No se pudo enviar el correo: {exc}'


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Usa la vista principal para evitar duplicar lógica
    return current_app.view_functions['login']()


@auth_bp.route('/logout')
def logout():
    return current_app.view_functions['logout']()


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (current_user.id,)).fetchone()

    if not user:
        conn.close()
        flash('No encontramos tu usuario en la base activa.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        telefono = request.form.get('telefono', '')
        email = request.form.get('email', '')
        observaciones = request.form.get('observaciones', '')
        nombre = request.form.get('nombre', user['nombre'])
        apellido = request.form.get('apellido', user['apellido'])
        nombre_completo = f"{nombre} {apellido}".strip() or user['nombre_completo']

        conn.execute(
            '''UPDATE usuarios SET telefono=?, email=?, observaciones=?, nombre=?, apellido=?, nombre_completo=? WHERE id=?''',
            (telefono, email, observaciones, nombre, apellido, nombre_completo, current_user.id),
        )
        conn.commit()
        flash('Perfil actualizado exitosamente', 'success')
        user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (current_user.id,)).fetchone()

    conn.close()
    return render_template('profile.html', user=user)


@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash('Las contraseñas no coinciden')
            return redirect(url_for('auth.change_password'))

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (current_user.id,)).fetchone()

        if not user:
            conn.close()
            flash('No encontramos tu usuario en la base activa.')
            return redirect(url_for('auth.change_password'))

        if not check_password_hash(user['password'], current_password) and user['password'] != current_password:
            flash('Contraseña actual incorrecta')
            conn.close()
            return redirect(url_for('auth.change_password'))

        conn.execute('UPDATE usuarios SET password=?, requiere_cambio_password=0 WHERE id=?',
                     (generate_password_hash(new_password), current_user.id))
        conn.commit()
        conn.close()

        flash('Contraseña cambiada exitosamente')
        return redirect(url_for('auth.profile'))

    return render_template('change_password.html')


@auth_bp.route('/auth/credentials')
@login_required
def credentials_dashboard():
    conn = get_db_connection()
    users = conn.execute(
        "SELECT id, nombre_completo, email, rol, estado, ultimo_acceso, intentos_fallidos FROM usuarios ORDER BY rol, email"
    ).fetchall()
    conn.close()

    return render_template(
        'credential_center.html',
        users=users,
        default_admin=DEFAULT_ADMIN,
        demo_user=DEMO_USER,
        masked_default=mask_password(DEFAULT_ADMIN['password']),
        masked_demo=mask_password(DEMO_USER['password']),
        active_db=load_active_db_path(),
        db_options=list_available_dbs(),
    )


@auth_bp.route('/auth/credentials/reset', methods=['POST'])
@login_required
def reset_credentials():
    if getattr(current_user, "rol", "") == "demo":
        flash('La cuenta demo no puede modificar credenciales.', 'warning')
        return redirect(url_for('auth.credentials_dashboard'))

    email = request.form.get('email')
    new_password = request.form.get('new_password')
    send_email_flag = request.form.get('send_email') == '1'

    if not email or not new_password:
        flash('Debes ingresar email y nueva contraseña.', 'warning')
        return redirect(url_for('auth.credentials_dashboard'))

    conn = get_db_connection()
    row = conn.execute("SELECT id, nombre_completo, nombre, apellido FROM usuarios WHERE email=?", (email,)).fetchone()
    if not row:
        conn.close()
        flash('No se encontró un usuario con ese correo.', 'danger')
        return redirect(url_for('auth.credentials_dashboard'))

    conn.execute(
        "UPDATE usuarios SET password=?, requiere_cambio_password=0, intentos_fallidos=0 WHERE id=?",
        (generate_password_hash(new_password), row['id']),
    )
    conn.commit()
    conn.close()

    if send_email_flag:
        name = row['nombre_completo'] or f"{row['nombre'] or ''} {row['apellido'] or ''}".strip()
        ok, msg = send_credentials_email(email, name, new_password, load_active_db_path())
        flash(msg, 'success' if ok else 'warning')
    else:
        flash('Contraseña restablecida.', 'success')

    return redirect(url_for('auth.credentials_dashboard'))


@auth_bp.route('/auth/credentials/create_admin', methods=['POST'])
@login_required
def create_admin_user():
    if getattr(current_user, "rol", "") not in ("admin",):
        flash('Solo un administrador puede crear o actualizar usuarios admin.', 'warning')
        return redirect(url_for('auth.credentials_dashboard'))

    email = request.form.get('email') or DEFAULT_ADMIN['email']
    password = request.form.get('password') or DEFAULT_ADMIN['password']
    nombre = request.form.get('nombre') or DEFAULT_ADMIN['nombre']
    apellido = request.form.get('apellido') or DEFAULT_ADMIN['apellido']
    cedula = request.form.get('cedula') or DEFAULT_ADMIN['cedula']
    nombre_completo = request.form.get('nombre_completo') or f"{nombre} {apellido}".strip()

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM usuarios WHERE email=?", (email,))
    row = c.fetchone()

    hashed = generate_password_hash(password)
    if row:
        user_id = row['id']
        c.execute(
            """UPDATE usuarios SET cedula=?, nombre=?, apellido=?, nombre_completo=?, password=?, rol='admin', estado='activo'
               WHERE id=?""",
            (cedula, nombre, apellido, nombre_completo, hashed, user_id),
        )
    else:
        c.execute(
            """INSERT INTO usuarios (cedula, nombre, apellido, nombre_completo, email, password, rol, estado)
               VALUES (?, ?, ?, ?, ?, ?, 'admin', 'activo')""",
            (cedula, nombre, apellido, nombre_completo, email, hashed),
        )
        user_id = c.lastrowid

    c.execute("SELECT id FROM roles WHERE name='admin'")
    role = c.fetchone()
    if role:
        c.execute("INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role['id']))

    conn.commit()
    conn.close()
    flash('Usuario administrador listo.', 'success')
    return redirect(url_for('auth.credentials_dashboard'))


@auth_bp.route('/auth/credentials/db', methods=['POST'])
@login_required
def change_active_db():
    if getattr(current_user, "rol", "") == "demo":
        flash('La cuenta demo no puede cambiar la base de datos.', 'warning')
        return redirect(url_for('auth.credentials_dashboard'))

    new_db = request.form.get('db_path')
    if not new_db:
        flash('Selecciona una base de datos.', 'warning')
        return redirect(url_for('auth.credentials_dashboard'))

    save_active_db_path(new_db)
    from app import init_db, ensure_default_admin

    init_db()
    ensure_default_admin()
    flash('Base de datos actualizada y credenciales por defecto creadas.', 'info')
    return redirect(url_for('auth.credentials_dashboard'))


@auth_bp.route('/auth/credentials/send', methods=['POST'])
@login_required
def email_credentials():
    if getattr(current_user, "rol", "") == "demo":
        flash('La cuenta demo no puede enviar credenciales.', 'warning')
        return redirect(url_for('auth.credentials_dashboard'))

    email = request.form.get('email')
    plain_password = request.form.get('plain_password')

    if not email or not plain_password:
        flash('Indica el correo y la contraseña a enviar.', 'warning')
        return redirect(url_for('auth.credentials_dashboard'))

    conn = get_db_connection()
    row = conn.execute("SELECT nombre_completo, nombre, apellido FROM usuarios WHERE email=?", (email,)).fetchone()
    conn.close()

    name = email
    if row:
        name = row['nombre_completo'] or f"{row['nombre'] or ''} {row['apellido'] or ''}".strip() or email

    ok, msg = send_credentials_email(email, name, plain_password, load_active_db_path())
    flash(msg, 'success' if ok else 'warning')
    return redirect(url_for('auth.credentials_dashboard'))
