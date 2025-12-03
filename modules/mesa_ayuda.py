from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from modules.db_utils import get_db_connection

mesa_ayuda_bp = Blueprint('mesa_ayuda', __name__, template_folder='../templates', static_folder='../static')


@mesa_ayuda_bp.route('/mesa_ayuda')
def mesa_ayuda():
    conn = get_db_connection()
    tickets = conn.execute('SELECT * FROM tickets ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('mesa_ayuda.html', tickets=tickets)

@mesa_ayuda_bp.route('/ticket/new', methods=['GET', 'POST'])
def new_ticket():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        category = request.form['category']
        user_id = request.form.get('user_id', 1)  # Default user

        conn = get_db_connection()
        conn.execute('''INSERT INTO tickets (title, description, priority, category, user_id, status)
                       VALUES (?, ?, ?, ?, ?, 'Abierto')''',
                    (title, description, priority, category, user_id))
        conn.commit()
        conn.close()
        flash('Ticket creado exitosamente')
        return redirect(url_for('mesa_ayuda.mesa_ayuda'))
    return render_template('new_ticket.html')

@mesa_ayuda_bp.route('/ticket/<int:ticket_id>/edit', methods=['GET', 'POST'])
def edit_ticket(ticket_id):
    conn = get_db_connection()
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        category = request.form['category']
        status = request.form['status']
        solution = request.form.get('solution', '')

        conn.execute('''UPDATE tickets SET title=?, description=?, priority=?, category=?,
                       status=?, solution=?, updated_at=datetime('now') WHERE id=?''',
                    (title, description, priority, category, status, solution, ticket_id))
        conn.commit()
        conn.close()
        flash('Ticket actualizado exitosamente')
        return redirect(url_for('mesa_ayuda.mesa_ayuda'))

    ticket = conn.execute('SELECT * FROM tickets WHERE id=?', (ticket_id,)).fetchone()
    conn.close()
    return render_template('edit_ticket.html', ticket=ticket)

@mesa_ayuda_bp.route('/ticket/<int:ticket_id>/delete', methods=['POST'])
def delete_ticket(ticket_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM tickets WHERE id=?', (ticket_id,))
    conn.commit()
    conn.close()
    flash('Ticket eliminado exitosamente')
    return redirect(url_for('mesa_ayuda.mesa_ayuda'))

@mesa_ayuda_bp.route('/api/tickets', methods=['GET'])
def api_tickets():
    conn = get_db_connection()
    tickets = conn.execute('SELECT * FROM tickets').fetchall()
    conn.close()
    return jsonify([dict(ticket) for ticket in tickets])
