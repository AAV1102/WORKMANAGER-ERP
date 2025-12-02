from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
import sqlite3

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

def get_db_connection():
    conn = sqlite3.connect('workmanager_erp.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_notification(user_id, message, url=None):
    """
    Función helper para crear una notificación para un usuario.
    Puede ser llamada desde cualquier parte de la aplicación.
    """
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO notificaciones (user_id, message, url) VALUES (?, ?, ?)",
            (user_id, message, url)
        )
        conn.commit()
    except Exception as e:
        print(f"Error al crear notificación: {e}") # Log a un archivo en producción
    finally:
        conn.close()

@notifications_bp.route('/api/unread')
@login_required
def get_unread_notifications():
    """Devuelve las notificaciones no leídas del usuario actual en formato JSON."""
    conn = get_db_connection()
    notifications = conn.execute("""
        SELECT id, message, url, created_at FROM notificaciones
        WHERE user_id = ? AND is_read = 0
        ORDER BY created_at DESC
        LIMIT 10
    """, (current_user.id,)).fetchall()
    conn.close()
    
    return jsonify({
        'count': len(notifications),
        'notifications': [dict(n) for n in notifications]
    })

@notifications_bp.route('/api/mark_as_read', methods=['POST'])
@login_required
def mark_as_read():
    """Marca notificaciones específicas o todas como leídas."""
    data = request.get_json()
    notification_ids = data.get('ids', [])
    
    conn = get_db_connection()
    try:
        if notification_ids:
            # Asegurarse de que los IDs son enteros para evitar inyección SQL
            safe_ids = [int(id) for id in notification_ids]
            placeholders = ','.join('?' for _ in safe_ids)
            query = f"UPDATE notificaciones SET is_read = 1 WHERE user_id = ? AND id IN ({placeholders})"
            params = [current_user.id] + safe_ids
            conn.execute(query, params)
        else: # Si no se envían IDs, marca todas como leídas
            conn.execute("UPDATE notificaciones SET is_read = 1 WHERE user_id = ?", (current_user.id,))
        
        conn.commit()
        return jsonify({'success': True})
    finally:
        conn.close()