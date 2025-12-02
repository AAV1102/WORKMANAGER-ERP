"""
EXTENSIONES PARA modules/inventarios.py
Agregar estas rutas a tu módulo existente
"""

from flask import Blueprint, request, jsonify, send_file
import sqlite3
from datetime import datetime
import pandas as pd
from io import BytesIO

# Crear blueprint (si lo usas independiente)
# Si lo integras en inventarios.py existente, usa el blueprint que ya tienes
extensiones_bp = Blueprint('extensiones_inventarios', __name__)

# ============================================================================
# NUEVAS RUTAS PARA BÚSQUEDA AVANZADA
# ============================================================================

@extensiones_bp.route('/api/buscar_serial_masivo', methods=['POST'])
def buscar_serial_masivo():
    """Buscar múltiples seriales a la vez"""
    try:
        data = request.get_json()
        seriales = data.get('seriales', [])
        
        if not seriales:
            return jsonify({'success': False, 'error': 'No se proporcionaron seriales'}), 400
        
        conn = sqlite3.connect('workmanager_erp.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        placeholders = ','.join(['?' for _ in seriales])
        query = f"""
            SELECT * FROM equipos_individuales 
            WHERE serial IN ({placeholders})
        """
        
        cursor.execute(query, seriales)
        rows = cursor.fetchall()
        resultados = [dict(row) for row in rows]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total': len(resultados),
            'encontrados': len(resultados),
            'no_encontrados': len(seriales) - len(resultados),
            'data': resultados
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@extensiones_bp.route('/api/estadisticas_completas')
def estadisticas_completas():
    """Estadísticas detalladas del inventario"""
    try:
        conn = sqlite3.connect('workmanager_erp.db')
        cursor = conn.cursor()
        
        # Total
        cursor.execute("SELECT COUNT(*) FROM equipos_individuales")
        total = cursor.fetchone()[0]
        
        # Por estado
        cursor.execute("""
            SELECT estado, COUNT(*) 
            FROM equipos_individuales 
            WHERE estado IS NOT NULL
            GROUP BY estado
        """)
        por_estado = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Por sede
        cursor.execute("""
            SELECT s.nombre, COUNT(ei.id) as total
            FROM equipos_individuales ei
            LEFT JOIN sedes s ON ei.sede_id = s.id
            WHERE s.nombre IS NOT NULL
            GROUP BY s.nombre
            ORDER BY total DESC
        """)
        por_sede = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Por tecnología
        cursor.execute("""
            SELECT tecnologia, COUNT(*) 
            FROM equipos_individuales 
            WHERE tecnologia IS NOT NULL
            GROUP BY tecnologia
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        por_tecnologia = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Asignados vs Disponibles
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN asignado_nuevo IS NOT NULL AND asignado_nuevo != '' THEN 1 ELSE 0 END) as asignados,
                SUM(CASE WHEN disponible = 'Si' THEN 1 ELSE 0 END) as disponibles
            FROM equipos_individuales
        """)
        row = cursor.fetchone()
        asignados = row[0] or 0
        disponibles = row[1] or 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'total_equipos': total,
                'asignados': asignados,
                'disponibles': disponibles,
                'por_estado': por_estado,
                'por_sede': por_sede,
                'por_tecnologia': por_tecnologia
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@extensiones_bp.route('/api/equipos_empleado/<cedula>')
def equipos_empleado(cedula):
    """Obtener todos los equipos asignados a un empleado"""
    try:
        conn = sqlite3.connect('workmanager_erp.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Obtener empleado
        cursor.execute("SELECT * FROM empleados WHERE cedula = ?", (cedula,))
        empleado = cursor.fetchone()
        
        if not empleado:
            return jsonify({'success': False, 'error': 'Empleado no encontrado'}), 404
        
        empleado_dict = dict(empleado)
        
        # Obtener equipos
        cursor.execute("""
            SELECT * FROM equipos_individuales 
            WHERE asignado_nuevo LIKE ?
        """, (f'%{empleado_dict["nombre"]}%',))
        
        equipos = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'empleado': empleado_dict,
            'total_equipos': len(equipos),
            'equipos': equipos
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@extensiones_bp.route('/api/exportar_inventario_completo')
def exportar_inventario_completo():
    """Exportar inventario completo a Excel"""
    try:
        conn = sqlite3.connect('workmanager_erp.db')
        
        # Cargar datos
        df = pd.read_sql_query("""
            SELECT 
                ei.*,
                s.nombre as sede_nombre,
                s.ciudad as sede_ciudad
            FROM equipos_individuales ei
            LEFT JOIN sedes s ON ei.sede_id = s.id
            ORDER BY ei.id DESC
        """, conn)
        
        conn.close()
        
        # Crear Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Inventario Completo', index=False)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'inventario_completo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# PARA INTEGRAR EN TU modules/inventarios.py EXISTENTE
# ============================================================================
"""
Copia estas funciones al final de tu archivo modules/inventarios.py:

1. buscar_serial_masivo
2. estadisticas_completas
3. equipos_empleado
4. exportar_inventario_completo

Y registra las rutas en tu blueprint inventarios_bp:

@inventarios_bp.route('/api/buscar_serial_masivo', methods=['POST'])
def buscar_serial_masivo():
    # ... código de la función

@inventarios_bp.route('/api/estadisticas_completas')
def estadisticas_completas():
    # ... código de la función

@inventarios_bp.route('/api/equipos_empleado/<cedula>')
def equipos_empleado(cedula):
    # ... código de la función

@inventarios_bp.route('/api/exportar_inventario_completo')
def exportar_inventario_completo():
    # ... código de la función
"""