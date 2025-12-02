from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3

sistemas_bp = Blueprint('sistemas', __name__, template_folder='../templates', static_folder='../static')

@sistemas_bp.route('/sistemas')
def sistemas():
    conn = sqlite3.connect('workmanager_erp.db')
    c = conn.cursor()

    # Get statistics for dashboard
    c.execute("SELECT COUNT(*) FROM tickets WHERE estado = 'abierto'")
    tickets_abiertos = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM tickets WHERE prioridad = 'alta' AND estado = 'abierto'")
    tickets_alta_prioridad = c.fetchone()[0]

    # Get real data from inventory and licenses
    # Count total equipment
    c.execute("SELECT COUNT(*) FROM equipos_agrupados")
    total_agrupados = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM equipos_individuales")
    total_individuales = c.fetchone()[0]

    total_equipos = total_agrupados + total_individuales

    # Count available equipment
    c.execute("SELECT COUNT(*) FROM equipos_agrupados WHERE estado_general = 'disponible'")
    disponibles_agrupados = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE estado = 'disponible'")
    disponibles_individuales = c.fetchone()[0]

    equipos_disponibles = disponibles_agrupados + disponibles_individuales

    # Count licenses
    c.execute("SELECT COUNT(*) FROM licencias_office365 WHERE estado = 'activa'")
    licencias_activas = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM licencias_office365")
    total_licencias = c.fetchone()[0]

    # Mock data for servers (in a real implementation, this would come from monitoring systems)
    servidores_online = 2
    total_servidores = 3
    uptime_promedio = 99.8

    # Get recent tickets
    c.execute("SELECT * FROM tickets ORDER BY fecha_apertura DESC LIMIT 5")
    tickets_recientes = c.fetchall()

    conn.close()

    return render_template('sistemas.html',
                         tickets_abiertos=tickets_abiertos,
                         tickets_alta_prioridad=tickets_alta_prioridad,
                         servidores_online=servidores_online,
                         total_servidores=total_servidores,
                         uptime_promedio=uptime_promedio,
                         licencias_disponibles=licencias_activas,
                         total_licencias=total_licencias,
                         total_equipos=total_equipos,
                         equipos_disponibles=equipos_disponibles,
                         tickets_recientes=tickets_recientes)

@sistemas_bp.route('/sistema/new', methods=['GET', 'POST'])
def new_sistema():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        version = request.form['version']
        conn = sqlite3.connect('todo.db')
        c = conn.cursor()
        c.execute("INSERT INTO sistemas (name, description, version) VALUES (?, ?, ?)", (name, description, version))
        conn.commit()
        conn.close()
        flash('Sistema added successfully')
        return redirect(url_for('sistemas.sistemas'))
    return render_template('new_sistema.html')

@sistemas_bp.route('/sistema/<int:sistema_id>/edit', methods=['GET', 'POST'])
def edit_sistema(sistema_id):
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        version = request.form['version']
        c.execute("UPDATE sistemas SET name=?, description=?, version=? WHERE id=?", (name, description, version, sistema_id))
        conn.commit()
        conn.close()
        flash('Sistema updated successfully')
        return redirect(url_for('sistemas.sistemas'))
    c.execute("SELECT * FROM sistemas WHERE id=?", (sistema_id,))
    sistema = c.fetchone()
    conn.close()
    return render_template('edit_sistema.html', sistema=sistema)

@sistemas_bp.route('/sistema/<int:sistema_id>/delete', methods=['POST'])
def delete_sistema(sistema_id):
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute("DELETE FROM sistemas WHERE id=?", (sistema_id,))
    conn.commit()
    conn.close()
    flash('Sistema deleted successfully')
    return redirect(url_for('sistemas.sistemas'))

@sistemas_bp.route('/api/sistemas', methods=['GET'])
def api_sistemas():
    conn = sqlite3.connect('todo.db')
    c = conn.cursor()
    c.execute("SELECT * FROM sistemas")
    sistemas = c.fetchall()
    conn.close()
    return jsonify(sistemas)

# Add more CRUD operations as needed
