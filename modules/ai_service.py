from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import requests
import json
from datetime import datetime

ai_service_bp = Blueprint('ai_service', __name__, template_folder='../templates', static_folder='../static')

def get_db_connection():
    conn = sqlite3.connect('workmanager_erp.db')
    conn.row_factory = sqlite3.Row
    return conn


def _get_inventory_agent_stats(conn):
    """Construye métricas del agente de inventario para los dashboards."""
    cur = conn.cursor()
    try:
        total_queries = cur.execute(
            'SELECT COUNT(*) FROM ai_logs WHERE category = "inventory"').fetchone()[0]
        successful = cur.execute(
            'SELECT COUNT(*) FROM ai_logs WHERE category = "inventory" AND status = "success"').fetchone()[0]
        last_activity = cur.execute(
            'SELECT MAX(created_at) FROM ai_logs WHERE category = "inventory"').fetchone()[0]
        return {
            'total_queries': total_queries or 0,
            'successful_responses': successful or 0,
            'last_activity': last_activity
        }
    except Exception:
        return {
            'total_queries': 0,
            'successful_responses': 0,
            'last_activity': None
        }

@ai_service_bp.route('/ai_service')
def ai_service():
    conn = get_db_connection()

    # Get AI logs
    ai_logs = conn.execute('SELECT * FROM ai_logs ORDER BY created_at DESC LIMIT 50').fetchall()

    # Get WhatsApp bot status
    whatsapp_status = "Activo"

    # Inventory agent stats
    inventory_agent_stats = _get_inventory_agent_stats(conn)

    conn.close()

    return render_template('ai_service.html',
                         ai_logs=ai_logs,
                         whatsapp_status=whatsapp_status,
                         inventory_agent_stats=inventory_agent_stats)

@ai_service_bp.route('/ai_log/new', methods=['GET', 'POST'])
def new_ai_log():
    if request.method == 'POST':
        query = request.form['query']
        response = request.form['response']
        conn = sqlite3.connect('workmanager_erp.db')
        c = conn.cursor()
        c.execute("INSERT INTO ai_logs (query, response) VALUES (?, ?)", (query, response))
        conn.commit()
        conn.close()
        flash('AI Log added successfully')
        return redirect(url_for('ai_service.ai_service'))
    return render_template('new_ai_log.html')

@ai_service_bp.route('/ai_log/<int:ai_log_id>/edit', methods=['GET', 'POST'])
def edit_ai_log(ai_log_id):
    conn = sqlite3.connect('workmanager_erp.db')
    c = conn.cursor()
    if request.method == 'POST':
        query = request.form['query']
        response = request.form['response']
        c.execute("UPDATE ai_logs SET query=?, response=? WHERE id=?", (query, response, ai_log_id))
        conn.commit()
        conn.close()
        flash('AI Log updated successfully')
        return redirect(url_for('ai_service.ai_service'))
    c.execute("SELECT * FROM ai_logs WHERE id=?", (ai_log_id,))
    ai_log = c.fetchone()
    conn.close()
    return render_template('edit_ai_log.html', ai_log=ai_log)

@ai_service_bp.route('/ai_log/<int:ai_log_id>/delete', methods=['POST'])
def delete_ai_log(ai_log_id):
    conn = sqlite3.connect('workmanager_erp.db')
    c = conn.cursor()
    c.execute("DELETE FROM ai_logs WHERE id=?", (ai_log_id,))
    conn.commit()
    conn.close()
    flash('AI Log deleted successfully')
    return redirect(url_for('ai_service.ai_service'))

@ai_service_bp.route('/api/ai_logs', methods=['GET'])
def api_ai_logs():
    conn = sqlite3.connect('workmanager_erp.db')
    c = conn.cursor()
    c.execute("SELECT * FROM ai_logs")
    ai_logs = c.fetchall()
    conn.close()
    return jsonify(ai_logs)

@ai_service_bp.route('/ai_detector', methods=['GET', 'POST'])
def ai_detector():
    result = None
    if request.method == 'POST':
        text = request.form.get('text', '')
        if text:
            # AI Detection logic (placeholder - integrate with actual AI detection service)
            result = detect_ai_generated_content(text)
    conn = get_db_connection()
    stats = _get_inventory_agent_stats(conn)
    conn.close()
    return render_template('ai_service.html', section='detector', result=result,
                           inventory_agent_stats=stats)

@ai_service_bp.route('/ai_corrector', methods=['GET', 'POST'])
def ai_corrector():
    corrected_text = None
    if request.method == 'POST':
        text = request.form.get('text', '')
        if text:
            # AI Correction logic (placeholder - integrate with actual AI correction service)
            corrected_text = correct_text_with_ai(text)
    conn = get_db_connection()
    stats = _get_inventory_agent_stats(conn)
    conn.close()
    return render_template('ai_service.html', section='corrector', corrected_text=corrected_text,
                           inventory_agent_stats=stats)

@ai_service_bp.route('/api/ai_detect', methods=['POST'])
def api_ai_detect():
    data = request.get_json()
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    result = detect_ai_generated_content(text)
    return jsonify(result)

@ai_service_bp.route('/api/ai_correct', methods=['POST'])
def api_ai_correct():
    data = request.get_json()
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    corrected_text = correct_text_with_ai(text)
    return jsonify({'corrected_text': corrected_text})

def detect_ai_generated_content(text):
    """AI Detection function - placeholder for actual implementation"""
    # This would integrate with services like OpenAI's detector, GPTZero, etc.
    # For now, return a mock result
    import random
    confidence = random.uniform(0.1, 0.9)
    is_ai_generated = confidence > 0.5

    return {
        'is_ai_generated': is_ai_generated,
        'confidence': round(confidence * 100, 2),
        'analysis': f"El texto {'parece ser generado por IA' if is_ai_generated else 'parece ser escrito por un humano'} con {round(confidence * 100, 2)}% de confianza.",
        'details': {
            'perplexity_score': random.uniform(10, 100),
            'burstiness_score': random.uniform(0.1, 0.9),
            'repetitiveness': random.uniform(0.1, 0.8)
        }
    }

def correct_text_with_ai(text):
    """AI Text Correction function - placeholder for actual implementation"""
    # This would integrate with services like Grammarly API, ChatGPT, etc.
    # For now, return a mock corrected version
    corrections = {
        'errores': ['error1', 'error2'],
        'sugerencias': ['suggestion1', 'suggestion2'],
        'texto_corregido': text + " [Texto corregido por IA]"
    }

    return corrections

# Add more CRUD operations as needed
