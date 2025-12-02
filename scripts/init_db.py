#!/usr/bin/env python3
"""
WORKMANAGER ERP - Script de inicialización de base de datos
"""

import sqlite3
import os
import sys
from datetime import datetime

def create_tables():
    """Crea todas las tablas necesarias para el sistema ERP"""

    # Conectar a la base de datos
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'todo.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("🚀 Inicializando base de datos WORKMANAGER ERP...")

        # Tabla de usuarios
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                document TEXT,
                phone TEXT,
                position TEXT,
                department TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de inventarios tecnológicos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                brand TEXT,
                model TEXT,
                serial_number TEXT UNIQUE,
                purchase_date DATE,
                warranty_expiry DATE,
                location TEXT,
                status TEXT DEFAULT 'Disponible',
                user_id INTEGER,
                assignment_date DATE,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Tabla de asignaciones
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                assigned_date DATE NOT NULL,
                return_date DATE,
                status TEXT DEFAULT 'Activa',
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inventory_id) REFERENCES inventarios (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Tabla de sistemas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sistemas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                version TEXT,
                category TEXT,
                status TEXT DEFAULT 'Activo',
                responsible_user_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (responsible_user_id) REFERENCES users (id)
            )
        ''')

        # Tabla de empleados (gestión humana)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empleados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                document TEXT UNIQUE,
                email TEXT,
                phone TEXT,
                position TEXT,
                department TEXT,
                salary REAL,
                hire_date DATE,
                status TEXT DEFAULT 'Activo',
                manager_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manager_id) REFERENCES empleados (id)
            )
        ''')

        # Tabla de pacientes (médico)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                document TEXT UNIQUE,
                birth_date DATE,
                gender TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                emergency_contact TEXT,
                blood_type TEXT,
                allergies TEXT,
                medical_history TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de equipos biomédicos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                brand TEXT,
                model TEXT,
                serial_number TEXT UNIQUE,
                purchase_date DATE,
                warranty_expiry DATE,
                location TEXT,
                status TEXT DEFAULT 'Operativo',
                last_maintenance DATE,
                next_maintenance DATE,
                responsible_user_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (responsible_user_id) REFERENCES users (id)
            )
        ''')

        # Tabla de licencias de software
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS licencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                software_name TEXT NOT NULL,
                license_key TEXT,
                version TEXT,
                category TEXT,
                purchase_date DATE,
                expiry_date DATE,
                status TEXT DEFAULT 'Activa',
                assigned_user_id INTEGER,
                cost REAL,
                vendor TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assigned_user_id) REFERENCES users (id)
            )
        ''')

        # Tabla de logs de IA
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                response TEXT,
                user_id INTEGER,
                module TEXT,
                success BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

        # Tabla de tickets de mesa de ayuda
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT NOT NULL,
                category TEXT NOT NULL,
                user_id INTEGER,
                status TEXT DEFAULT 'Abierto',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                solution TEXT,
                assigned_user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (assigned_user_id) REFERENCES users (id)
            )
        ''')

        # Tabla de tareas (para compatibilidad)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insertar datos de ejemplo
        print("📝 Insertando datos de ejemplo...")

        # Usuario administrador
        cursor.execute('''
            INSERT OR IGNORE INTO users (name, email, document, position, department)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Administrador', 'admin@workmanager.com', '123456789', 'Administrador', 'Sistemas'))

        # Usuario de ejemplo
        cursor.execute('''
            INSERT OR IGNORE INTO users (name, email, document, position, department)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Juan Pérez', 'juan.perez@empresa.com', '987654321', 'Desarrollador', 'Tecnología'))

        # Equipo de ejemplo
        cursor.execute('''
            INSERT OR IGNORE INTO inventarios (name, description, category, brand, model, serial_number, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Laptop Dell', 'Laptop para desarrollo', 'Computadora', 'Dell', 'Latitude 5420', 'DELL001', 'Disponible'))

        # Licencia de ejemplo
        cursor.execute('''
            INSERT OR IGNORE INTO licencias (software_name, license_key, version, category, expiry_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Microsoft Office', 'XXXXX-XXXXX-XXXXX-XXXXX-XXXXX', '2021', 'Ofimática', '2025-12-31', 'Activa'))

        # Ticket de ejemplo
        cursor.execute('''
            INSERT OR IGNORE INTO tickets (title, description, priority, category, status)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Problema con impresora', 'La impresora no responde en el piso 3', 'Media', 'Técnico', 'Abierto'))

        # Confirmar cambios
        conn.commit()

        print("✅ Base de datos inicializada correctamente!")
        print("📊 Tablas creadas:")
        print("   - users (usuarios)")
        print("   - inventarios (inventario tecnológico)")
        print("   - assignments (asignaciones)")
        print("   - sistemas (sistemas informáticos)")
        print("   - empleados (gestión humana)")
        print("   - pacientes (registros médicos)")
        print("   - equipos (biomédica)")
        print("   - licencias (licencias de software)")
        print("   - ai_logs (logs de IA)")
        print("   - tickets (mesa de ayuda)")
        print("   - tasks (compatibilidad)")
        print("\n🎯 Datos de ejemplo insertados!")

    except Exception as e:
        print(f"❌ Error al crear las tablas: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()

    return True

def main():
    """Función principal"""
    print("=" * 60)
    print("WORKMANAGER ERP - Inicialización de Base de Datos")
    print("=" * 60)

    success = create_tables()

    if success:
        print("\n🎉 ¡Base de datos lista para usar!")
        print("🚀 Ejecuta 'python run.py' para iniciar la aplicación")
    else:
        print("\n💥 Error en la inicialización. Revisa los logs anteriores.")
        sys.exit(1)

if __name__ == '__main__':
    main()
