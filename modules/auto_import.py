from flask import Blueprint, request, jsonify, render_template
import os
import json
from scripts.auto_import_inventory import AutoInventoryImporter
import logging

auto_import_bp = Blueprint('auto_import', __name__)

@auto_import_bp.route('/auto_import')
def auto_import_interface():
    """Render the auto import interface"""
    return render_template('auto_import_interface.html')

@auto_import_bp.route('/api/auto_import', methods=['POST'])
def api_auto_import():
    """API endpoint for automatic inventory import"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not file.filename.endswith('.json'):
            return jsonify({'success': False, 'error': 'File must be JSON'}), 400

        # Save uploaded file temporarily
        temp_path = os.path.join('uploads', 'temp_import.json')
        os.makedirs('uploads', exist_ok=True)
        file.save(temp_path)

        # Initialize importer
        importer = AutoInventoryImporter()

        # Import data
        stats = importer.import_from_json(temp_path)

        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

        if stats:
            logging.info(f"Auto import completed successfully: {stats}")
            return jsonify({
                'success': True,
                'stats': stats,
                'message': 'Importación completada exitosamente'
            })
        else:
            return jsonify({'success': False, 'error': 'Import failed'}), 500

    except Exception as e:
        logging.error(f"Auto import error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@auto_import_bp.route('/api/auto_import/status', methods=['GET'])
def get_import_status():
    """Get the status of current imports"""
    # This could be expanded to show real-time progress
    return jsonify({
        'status': 'idle',
        'last_import': None,
        'message': 'No hay importaciones activas'
    })
