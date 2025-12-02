#!/usr/bin/env python3
"""
Script para integrar Grok Code AI en WORKMANAGER ERP
Agrega soporte para Grok junto a ChatGPT existente
"""

import os
import sqlite3
from datetime import datetime

DB_PATH = 'workmanager_erp.db'

def get_db_connection():
    """Conecta a la base de datos"""
    return sqlite3.connect(DB_PATH)

def update_ai_service_module():
    """Actualiza el módulo ai_service para incluir Grok"""
    ai_service_path = 'modules/ai_service.py'

    if not os.path.exists(ai_service_path):
        print(f"❌ Módulo ai_service no encontrado: {ai_service_path}")
        return False

    # Leer archivo actual
    with open(ai_service_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verificar si ya tiene Grok
    if 'grok' in content.lower():
        print("✅ Módulo ai_service ya tiene soporte para Grok")
        return True

    # Agregar import de groq
    if 'import openai' in content:
        content = content.replace('import openai', 'import openai\nimport groq')

    # Agregar función para Grok
    grok_function = '''
@ai_service_bp.route('/api/ai/grok', methods=['POST'])
def api_ai_grok():
    """API endpoint para consultas con Grok"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        module = data.get('module', 'general')
        user_id = data.get('user_id')

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Configurar Grok
        groq_api_key = os.environ.get('GROQ_API_KEY')
        if not groq_api_key:
            return jsonify({'error': 'Grok API key not configured'}), 500

        client = groq.Grok(api_key=groq_api_key)

        # Hacer consulta
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": f"You are a helpful AI assistant specialized in {module} management for WORKMANAGER ERP."},
                {"role": "user", "content": query}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        ai_response = response.choices[0].message.content

        # Guardar en logs
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO ai_logs (query, response, user_id, module, category, status)
            VALUES (?, ?, ?, ?, 'grok', 'success')
        ''', (query, ai_response, user_id, module))
        conn.commit()
        conn.close()

        return jsonify({
            'response': ai_response,
            'provider': 'grok',
            'model': 'mixtral-8x7b-32768'
        })

    except Exception as e:
        # Log error
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO ai_logs (query, response, user_id, module, category, status)
            VALUES (?, ?, ?, ?, 'grok', 'error')
        ''', (query, str(e), user_id, module))
        conn.commit()
        conn.close()

        return jsonify({'error': str(e)}), 500

@ai_service_bp.route('/api/ai/chatgpt', methods=['POST'])
def api_ai_chatgpt():
    """API endpoint para consultas con ChatGPT"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        module = data.get('module', 'general')
        user_id = data.get('user_id')

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Configurar OpenAI
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            return jsonify({'error': 'OpenAI API key not configured'}), 500

        openai.api_key = openai_api_key

        # Hacer consulta
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a helpful AI assistant specialized in {module} management for WORKMANAGER ERP."},
                {"role": "user", "content": query}
            ],
            max_tokens=1000,
            temperature=0.7
        )

        ai_response = response.choices[0].message.content

        # Guardar en logs
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO ai_logs (query, response, user_id, module, category, status)
            VALUES (?, ?, ?, ?, 'chatgpt', 'success')
        ''', (query, ai_response, user_id, module))
        conn.commit()
        conn.close()

        return jsonify({
            'response': ai_response,
            'provider': 'openai',
            'model': 'gpt-3.5-turbo'
        })

    except Exception as e:
        # Log error
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO ai_logs (query, response, user_id, module, category, status)
            VALUES (?, ?, ?, ?, 'chatgpt', 'error')
        ''', (query, str(e), user_id, module))
        conn.commit()
        conn.close()

        return jsonify({'error': str(e)}), 500
'''

    # Agregar funciones después de la función existente api_ai_logs
    if 'def api_ai_logs():' in content:
        content = content.replace(
            'def api_ai_logs():',
            grok_function + '\n@ai_service_bp.route(\'/api/ai_logs\', methods=[\'GET\'])'
        )

    # Actualizar dashboard para mostrar ambas opciones
    dashboard_function = '''
@ai_service_bp.route('/ai_service')
def ai_service():
    conn = get_db_connection()

    # Get AI logs with provider info
    ai_logs = conn.execute('SELECT * FROM ai_logs ORDER BY created_at DESC LIMIT 50').fetchall()

    # Get stats by provider
    grok_stats = {
        'total_queries': conn.execute('SELECT COUNT(*) FROM ai_logs WHERE category = "grok"').fetchone()[0],
        'successful_responses': conn.execute('SELECT COUNT(*) FROM ai_logs WHERE category = "grok" AND status = "success"').fetchone()[0],
        'last_activity': conn.execute('SELECT MAX(created_at) FROM ai_logs WHERE category = "grok"').fetchone()[0]
    }

    chatgpt_stats = {
        'total_queries': conn.execute('SELECT COUNT(*) FROM ai_logs WHERE category = "chatgpt"').fetchone()[0],
        'successful_responses': conn.execute('SELECT COUNT(*) FROM ai_logs WHERE category = "chatgpt" AND status = "success"').fetchone()[0],
        'last_activity': conn.execute('SELECT MAX(created_at) FROM ai_logs WHERE category = "chatgpt"').fetchone()[0]
    }

    # Legacy stats for backward compatibility
    inventory_agent_stats = {
        'total_queries': grok_stats['total_queries'] + chatgpt_stats['total_queries'],
        'successful_responses': grok_stats['successful_responses'] + chatgpt_stats['successful_responses'],
        'last_activity': max(grok_stats['last_activity'] or '1970-01-01', chatgpt_stats['last_activity'] or '1970-01-01')
    }

    conn.close()

    return render_template('ai_service.html',
                         ai_logs=ai_logs,
                         grok_stats=grok_stats,
                         chatgpt_stats=chatgpt_stats,
                         inventory_agent_stats=inventory_agent_stats)
'''

    # Reemplazar función dashboard
    if 'def ai_service():' in content:
        # Encontrar el final de la función
        start = content.find('def ai_service():')
        # Buscar el final de la función (siguiente def o final del archivo)
        next_def = content.find('\ndef ', start + 1)
        if next_def == -1:
            next_def = len(content)

        old_function = content[start:next_def]
        content = content.replace(old_function, dashboard_function)

    # Escribir archivo actualizado
    with open(ai_service_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ Módulo ai_service actualizado con soporte para Grok")
    return True

def update_ai_template():
    """Actualiza el template de AI service para incluir selección de agente"""
    template_path = 'templates/ai_service.html'

    if not os.path.exists(template_path):
        print(f"❌ Template ai_service no encontrado: {template_path}")
        return False

    # Leer template
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verificar si ya tiene selección de agente
    if 'select-agent' in content:
        print("✅ Template ya tiene selección de agente")
        return True

    # Agregar selector de agente después del título
    selector_html = '''
    <!-- AI Agent Selector -->
    <div class="row mb-4">
        <div class="col-md-12">
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-robot"></i> Seleccionar Agente IA</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="aiAgent" id="grokAgent" value="grok" checked>
                                <label class="form-check-label" for="grokAgent">
                                    <strong>Grok Code AI</strong><br>
                                    <small class="text-muted">Agente especializado de xAI, excelente para análisis técnico</small>
                                </label>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-check">
                                <input class="form-check-input" type="radio" name="aiAgent" id="chatgptAgent" value="chatgpt">
                                <label class="form-check-label" for="chatgptAgent">
                                    <strong>ChatGPT</strong><br>
                                    <small class="text-muted">Agente versátil de OpenAI, bueno para consultas generales</small>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''

    # Agregar después del título
    if '<h2>AI Service</h2>' in content:
        content = content.replace('<h2>AI Service</h2>', '<h2>AI Service</h2>' + selector_html)

    # Actualizar JavaScript para usar el agente seleccionado
    js_update = '''
    function sendAIQuery() {
        const query = document.getElementById('aiQuery').value;
        const selectedAgent = document.querySelector('input[name="aiAgent"]:checked').value;

        if (!query.trim()) {
            alert('Por favor ingresa una consulta');
            return;
        }

        // Mostrar loading
        document.getElementById('aiResponse').innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Procesando...</div>';

        fetch(`/ai_service/api/ai/${selectedAgent}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                module: 'general',
                user_id: 1  // TODO: obtener del usuario actual
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('aiResponse').innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            } else {
                document.getElementById('aiResponse').innerHTML = `
                    <div class="card">
                        <div class="card-header">
                            <strong>Respuesta de ${data.provider} (${data.model})</strong>
                        </div>
                        <div class="card-body">
                            ${data.response.replace(/\n/g, '<br>')}
                        </div>
                    </div>
                `;
            }
        })
        .catch(error => {
            document.getElementById('aiResponse').innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
        });
    }
    '''

    # Reemplazar función sendAIQuery existente
    if 'function sendAIQuery()' in content:
        # Encontrar y reemplazar la función
        start = content.find('function sendAIQuery()')
        end = content.find('}', start) + 1
        old_function = content[start:end]
        content = content.replace(old_function, js_update)

    # Escribir template actualizado
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ Template ai_service actualizado con selección de agente")
    return True

def update_config_for_grok():
    """Actualiza configuración para incluir Grok"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Agregar configuración de Grok si no existe
        cur.execute("SELECT id FROM config WHERE `key` = 'grok_api_key'")
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO config (`key`, `value`, description)
                VALUES ('grok_api_key', '', 'API Key para Grok Code AI')
            """)

        cur.execute("SELECT id FROM config WHERE `key` = 'grok_model'")
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO config (`key`, `value`, description)
                VALUES ('grok_model', 'mixtral-8x7b-32768', 'Modelo de Grok a utilizar')
            """)

        conn.commit()
        print("✅ Configuración de Grok agregada")

    except Exception as e:
        print(f"❌ Error actualizando configuración: {e}")
    finally:
        conn.close()

def main():
    """Función principal"""
    print("🤖 WORKMANAGER ERP - Integrar Grok Code AI")
    print("=" * 45)

    success = True

    # Actualizar módulo ai_service
    if not update_ai_service_module():
        success = False

    # Actualizar template
    if not update_ai_template():
        success = False

    # Actualizar configuración
    update_config_for_grok()

    if success:
        print("\n✅ Integración de Grok completada")
        print("\n📋 Cambios realizados:")
        print("- Agregado soporte para Grok en ai_service.py")
        print("- Actualizado template con selector de agente")
        print("- Agregada configuración para Grok")
        print("\n🔑 Recuerda configurar GROQ_API_KEY en tu archivo .env")
        print("\n🎯 Ahora puedes alternar entre ChatGPT y Grok en el módulo AI Service")
    else:
        print("\n❌ Algunos componentes no pudieron actualizarse")

if __name__ == "__main__":
    main()
