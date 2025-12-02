#!/usr/bin/env python3
"""
WORKMANAGER ERP - Script de ejecución principal
"""

import os
import sys
from app import app

def main():
    """Función principal para ejecutar la aplicación"""
    try:
        # Configurar puerto desde variable de entorno o usar 5000 por defecto
        port = int(os.environ.get('PORT', 5000))

        # Configurar host (0.0.0.0 para acceso externo, 127.0.0.1 para local)
        host = os.environ.get('HOST', '127.0.0.1')

        # Configurar modo debug
        debug = os.environ.get('DEBUG', 'True').lower() == 'true'

        print("🚀 Iniciando WORKMANAGER ERP...")
        print(f"📍 Servidor: http://{host}:{port}")
        print(f"🔧 Modo debug: {debug}")
        print("📊 Módulos cargados: Usuarios, Inventarios, Sistemas, RRHH, Médico, Biomédica, Licencias, AI, Mesa de Ayuda")
        print("=" * 60)

        # Ejecutar la aplicación
        app.run(host=host, port=port, debug=debug)

    except KeyboardInterrupt:
        print("\n👋 Aplicación detenida por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error al iniciar la aplicación: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
