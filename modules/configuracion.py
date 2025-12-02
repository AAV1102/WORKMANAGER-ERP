from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import os
from config import Config
from flask import current_app
from modules.db_utils import get_db_connection

configuracion_bp = Blueprint('configuracion', __name__, template_folder='../templates', static_folder='../static')

@configuracion_bp.route('/configuracion')
def configuracion():
    """Página principal de configuración del sistema"""
    conn = get_db_connection()

    # Obtener configuraciones actuales
    config_items = conn.execute('SELECT * FROM config ORDER BY `key`').fetchall()

    # Obtener configuraciones de APIs
    api_configs = {
        'openai_api_key': os.environ.get('OPENAI_API_KEY', ''),
        'groq_api_key': os.environ.get('GROQ_API_KEY', ''),
        'whatsapp_api_url': os.environ.get('WHATSAPP_API_URL', ''),
        'whatsapp_token': os.environ.get('WHATSAPP_TOKEN', ''),
        'zoho_desk_api_key': os.environ.get('ZOHO_DESK_API_KEY', ''),
        'ocs_inventory_url': os.environ.get('OCS_INVENTORY_URL', ''),
        'ocs_inventory_user': os.environ.get('OCS_INVENTORY_USER', ''),
        'ocs_inventory_password': os.environ.get('OCS_INVENTORY_PASSWORD', ''),
    }

    conn.close()

    return render_template('configuracion.html',
                         config_items=config_items,
                         api_configs=api_configs)

@configuracion_bp.route('/configuracion/truncate_table', methods=['POST'])
def truncate_table():
    data = request.get_json(silent=True) or {}
    table_param = data.get('tables') or data.get('table_name') or request.form.get('table_name')
    allowed = ['equipos_individuales', 'empleados', 'licencias_office365', 'inventario_bajas']

    if not table_param:
        return jsonify({'success': False, 'error': 'No se recibieron tablas a limpiar'}), 400

    if isinstance(table_param, (list, tuple)):
        tables = [t for t in table_param if t in allowed]
    else:
        tables = [table_param] if table_param in allowed else []

    if not tables:
        return jsonify({'success': False, 'error': 'Tabla no permitida'}), 400

    if not current_app.config.get('TESTING'):
        try:
            from flask_login import current_user
            if getattr(current_user, 'rol', '') != 'admin':
                return jsonify({'success': False, 'error': 'No autorizado'}), 403
        except Exception:
            return jsonify({'success': False, 'error': 'No autorizado'}), 403
    try:
        conn = get_db_connection()
        for table in tables:
            conn.execute(f'DELETE FROM {table}')
        conn.commit()
        conn.close()
        cleaned = ', '.join(tables)
        return jsonify({'success': True, 'message': f'Tabla(s) {cleaned} limpiada(s) exitosamente'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@configuracion_bp.route('/configuracion/update', methods=['POST'])
def update_config():
    """Actualizar configuraciones del sistema"""
    config_key = request.form['key']
    config_value = request.form['value']

    conn = get_db_connection()
    conn.execute('UPDATE config SET value = ?, updated_at = datetime("now") WHERE `key` = ?',
                (config_value, config_key))
    conn.commit()
    conn.close()

    flash(f'Configuración {config_key} actualizada exitosamente')
    return redirect(url_for('configuracion.configuracion'))

@configuracion_bp.route('/configuracion/api/update', methods=['POST'])
def update_api_config():
    """Actualizar configuraciones de APIs"""
    api_type = request.form['api_type']

    if api_type == 'openai':
        os.environ['OPENAI_API_KEY'] = request.form['openai_api_key']
    elif api_type == 'groq':
        os.environ['GROQ_API_KEY'] = request.form['groq_api_key']
    elif api_type == 'whatsapp':
        os.environ['WHATSAPP_API_URL'] = request.form['whatsapp_api_url']
        os.environ['WHATSAPP_TOKEN'] = request.form['whatsapp_token']
    elif api_type == 'zoho_desk':
        os.environ['ZOHO_DESK_API_KEY'] = request.form['zoho_desk_api_key']
    elif api_type == 'ocs_inventory':
        os.environ['OCS_INVENTORY_URL'] = request.form['ocs_inventory_url']
        os.environ['OCS_INVENTORY_USER'] = request.form['ocs_inventory_user']
        os.environ['OCS_INVENTORY_PASSWORD'] = request.form['ocs_inventory_password']

    flash(f'Configuración de {api_type} actualizada exitosamente')
    return redirect(url_for('configuracion.configuracion'))

@configuracion_bp.route('/configuracion/test/<api_type>', methods=['POST'])
def test_api_connection(api_type):
    """Probar conexión con APIs"""
    try:
        if api_type == 'openai':
            import openai
            openai.api_key = os.environ.get('OPENAI_API_KEY')
            # Test simple
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            return jsonify({'success': True, 'message': 'Conexión exitosa con OpenAI'})

        elif api_type == 'groq':
            import groq
            client = groq.Client(api_key=os.environ.get('GROQ_API_KEY'))
            response = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            return jsonify({'success': True, 'message': 'Conexión exitosa con Grok'})

        elif api_type == 'whatsapp':
            # Test WhatsApp API connection
            import requests
            url = os.environ.get('WHATSAPP_API_URL')
            token = os.environ.get('WHATSAPP_TOKEN')
            if url and token:
                response = requests.get(f"{url}/status", headers={'Authorization': f'Bearer {token}'})
                if response.status_code == 200:
                    return jsonify({'success': True, 'message': 'Conexión exitosa con WhatsApp API'})
            return jsonify({'success': False, 'message': 'Error en conexión con WhatsApp API'})

        elif api_type == 'zoho_desk':
            # Test Zoho Desk API connection
            import requests
            api_key = os.environ.get('ZOHO_DESK_API_KEY')
            if api_key:
                headers = {'Authorization': f'Zoho-oauthtoken {api_key}'}
                response = requests.get('https://desk.zoho.com/api/v1/tickets', headers=headers)
                if response.status_code == 200:
                    return jsonify({'success': True, 'message': 'Conexión exitosa con Zoho Desk'})
            return jsonify({'success': False, 'message': 'Error en conexión con Zoho Desk'})

        elif api_type == 'ocs_inventory':
            # Test OCS Inventory connection
            import requests
            url = os.environ.get('OCS_INVENTORY_URL')
            user = os.environ.get('OCS_INVENTORY_USER')
            password = os.environ.get('OCS_INVENTORY_PASSWORD')
            if url and user and password:
                response = requests.get(url, auth=(user, password))
                if response.status_code == 200:
                    return jsonify({'success': True, 'message': 'Conexión exitosa con OCS Inventory'})
            return jsonify({'success': False, 'message': 'Error en conexión con OCS Inventory'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

    return jsonify({'success': False, 'message': 'Tipo de API no reconocido'})

@configuracion_bp.route('/configuracion/backup', methods=['POST'])
def create_backup():
    """Crear backup de la base de datos"""
    import shutil
    from datetime import datetime

    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backup_{timestamp}.db'

        shutil.copy('workmanager_erp.db', backup_file)

        flash(f'Backup creado exitosamente: {backup_file}')
        return redirect(url_for('configuracion.configuracion'))

    except Exception as e:
        flash(f'Error al crear backup: {str(e)}')
        return redirect(url_for('configuracion.configuracion'))

@configuracion_bp.route('/configuracion/reset', methods=['POST'])
def reset_config():
    """Resetear configuraciones a valores por defecto"""
    conn = get_db_connection()

    # Reset system config
    default_configs = [
        ('system_version', '3.0'),
        ('company_name', 'Integral IPS'),
        ('db_version', '1.0'),
        ('smtp_host', 'smtp.gmail.com'),
        ('smtp_port', '587'),
        ('two_factor_required', '0'),
        ('session_timeout', '3600'),
        ('max_login_attempts', '5'),
        ('backup_retention_days', '30'),
        ('log_retention_days', '90'),
    ]

    for key, value in default_configs:
        conn.execute('UPDATE config SET value = ? WHERE `key` = ?', (value, key))

    conn.commit()
    conn.close()

    flash('Configuraciones reseteadas a valores por defecto')
    return redirect(url_for('configuracion.configuracion'))
