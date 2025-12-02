"""
WORKMANAGER ERP - Punto de entrada para servidores WSGI como Gunicorn.
Este script es para desarrollo local. En producción, Gunicorn llamará directamente a 'app:app'.
"""

import os
from app import app

if __name__ == '__main__':
    # Este bloque es para desarrollo local.
    # En producción, un servidor WSGI como Gunicorn importará 'app' directamente.
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print("="*60)
    print(f"🚀 Iniciando servidor de DESARROLLO en http://{host}:{port}")
    print(f"🔧 Modo debug: {debug}")
    print("="*60)
    app.run(host=host, port=port, debug=debug)
