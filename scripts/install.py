#!/usr/bin/env python3
"""
Script de instalación automática para WORKMANAGER ERP
Instala dependencias, configura base de datos y prepara el entorno.
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def run_command(command, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e}")
        print(f"Output: {e.output}")
        return False

def create_env_file():
    """Crea archivo .env con configuraciones básicas"""
    env_content = """# WORKMANAGER ERP - Configuración de Entorno

# Flask
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-in-production

# Base de datos
DATABASE_URL=sqlite:///workmanager_erp.db

# APIs (configurar según corresponda)
OPENAI_API_KEY=your-openai-key
GROQ_API_KEY=your-groq-key
WHATSAPP_API_URL=https://api.whatsapp.com
WHATSAPP_TOKEN=your-whatsapp-token
ZOHO_DESK_API_KEY=your-zoho-key
OCS_INVENTORY_URL=https://ocs.example.com
OCS_INVENTORY_USER=your-ocs-user
OCS_INVENTORY_PASSWORD=your-ocs-password

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password

# Configuración del sistema
COMPANY_NAME=Integral IPS
SYSTEM_VERSION=3.0
"""

    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("✅ Archivo .env creado")

def setup_database():
    """Configura la base de datos inicial"""
    print("\n🗄️ Configurando base de datos...")

    # Ejecutar init_db.py
    try:
        from app import init_db
        init_db()
        print("✅ Base de datos inicializada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        return False

def create_directories():
    """Crea directorios necesarios"""
    directories = [
        'uploads',
        'static/uploads',
        'logs',
        'backups',
        'temp'
    ]

    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Directorio creado: {dir_path}")

def install_dependencies():
    """Instala dependencias de Python"""
    print("\n📦 Instalando dependencias de Python...")

    # Verificar si requirements.txt existe
    if not os.path.exists('requirements.txt'):
        print("❌ No se encontró requirements.txt")
        return False

    # Instalar dependencias
    return run_command("pip install -r requirements.txt", "Instalación de dependencias")

def check_python_version():
    """Verifica la versión de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} no es compatible. Se requiere Python 3.8+")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detectado")
    return True

def main():
    """Función principal de instalación"""
    print("🚀 WORKMANAGER ERP - Instalación Automática")
    print("=" * 50)

    # Verificar Python
    if not check_python_version():
        sys.exit(1)

    # Instalar dependencias
    if not install_dependencies():
        print("❌ Falló la instalación de dependencias")
        sys.exit(1)

    # Crear directorios
    create_directories()

    # Crear archivo .env
    create_env_file()

    # Configurar base de datos
    if not setup_database():
        print("❌ Falló la configuración de la base de datos")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("🎉 ¡Instalación completada exitosamente!")
    print("\n📋 Próximos pasos:")
    print("1. Edita el archivo .env con tus configuraciones reales")
    print("2. Ejecuta: python run.py")
    print("3. Accede a http://localhost:5000")
    print("\n📖 Para más información, revisa el README.md")

if __name__ == "__main__":
    main()
