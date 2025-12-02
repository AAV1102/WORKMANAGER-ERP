"""
WORKMANAGER ERP - Configuración de la aplicación
"""

import os
from datetime import timedelta

class Config:
    """Configuración base de la aplicación"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

    # Base de datos
    DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///todo.db'

    # Sesión
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size for large CSV files

    # Export settings
    EXPORT_FORMATS = ['excel', 'pdf', 'csv', 'txt', 'barcode', 'life_sheet', 'image']

    # Pagination
    ITEMS_PER_PAGE = 25

    # AI Service
    AI_API_KEY = os.environ.get('AI_API_KEY')
    AI_MODEL = os.environ.get('AI_MODEL', 'gpt-3.5-turbo')

    # Email (para futuras implementaciones)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    DATABASE_URI = 'sqlite:///todo_dev.db'

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Debe estar configurada en producción

    # Base de datos de producción
    DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///todo_prod.db'

    # Configuraciones de seguridad adicionales
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True

class TestingConfig(Config):
    """Configuración para pruebas"""
    TESTING = True
    DEBUG = True
    DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Obtiene la configuración según el entorno"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    return config.get(config_name, config['default'])
