#!/usr/bin/env python3
"""
Script para resetear la base de datos de WORKMANAGER ERP
Elimina la base de datos actual y la recrea desde cero.
"""

import os
import sys
import sqlite3
from pathlib import Path

def confirm_reset():
    """Pide confirmación al usuario"""
    print("⚠️  ATENCIÓN: Esta acción eliminará TODOS los datos de la base de datos.")
    print("Se perderán:")
    print("- Todos los empleados")
    print("- Todo el inventario")
    print("- Todas las licencias")
    print("- Todos los tickets")
    print("- Todas las configuraciones personalizadas")
    print()

    response = input("¿Estás seguro de que quieres continuar? (escribe 'SI' para confirmar): ")
    return response.upper() == 'SI'

def backup_database():
    """Crea un backup de la base de datos actual"""
    db_file = 'workmanager_erp.db'
    if os.path.exists(db_file):
        import shutil
        from datetime import datetime

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backups/backup_{timestamp}.db'

        # Crear directorio de backups si no existe
        Path('backups').mkdir(exist_ok=True)

        shutil.copy2(db_file, backup_file)
        print(f"✅ Backup creado: {backup_file}")
        return backup_file
    return None

def remove_database():
    """Elimina la base de datos actual"""
    db_file = 'workmanager_erp.db'
    if os.path.exists(db_file):
        os.remove(db_file)
        print("✅ Base de datos eliminada")
        return True
    else:
        print("ℹ️  No se encontró base de datos para eliminar")
        return True

def recreate_database():
    """Recrea la base de datos desde cero"""
    print("🔄 Recreando base de datos...")

    try:
        # Importar y ejecutar init_db
        sys.path.append('..')
        from app import init_db

        init_db()
        print("✅ Base de datos recreada exitosamente")
        return True

    except Exception as e:
        print(f"❌ Error recreando base de datos: {e}")
        return False

def populate_sample_data():
    """Opcionalmente pobla con datos de ejemplo"""
    response = input("¿Quieres poblar con datos de ejemplo? (s/n): ").lower().strip()
    if response == 's':
        print("🔄 Poblando datos de ejemplo...")

        conn = sqlite3.connect('workmanager_erp.db')
        cur = conn.cursor()

        try:
            # Insertar sedes de ejemplo
            cur.execute("""
                INSERT OR IGNORE INTO sedes (codigo, nombre, ciudad, departamento, estado)
                VALUES
                ('SEDE001', 'Sede Principal Bogotá', 'Bogotá', 'Cundinamarca', 'activa'),
                ('SEDE002', 'Sede Norte Bogotá', 'Bogotá', 'Cundinamarca', 'activa'),
                ('SEDE003', 'Sede Medellín', 'Medellín', 'Antioquia', 'activa')
            """)

            # Insertar empleados de ejemplo
            cur.execute("""
                INSERT OR IGNORE INTO empleados (cedula, nombre, apellido, cargo, departamento, ciudad, estado)
                VALUES
                ('123456789', 'Juan', 'Pérez', 'Administrador', 'TI', 'Bogotá', 'activo'),
                ('987654321', 'María', 'García', 'Analista', 'RRHH', 'Bogotá', 'activo'),
                ('456789123', 'Carlos', 'Rodríguez', 'Técnico', 'Sistemas', 'Medellín', 'activo')
            """)

            # Insertar equipos de ejemplo
            cur.execute("""
                INSERT OR IGNORE INTO equipos_individuales (
                    codigo_barras_individual, tecnologia, marca, modelo, serial,
                    estado, disponible, sede_id, creador_registro
                ) VALUES
                ('BOG-CPU-001', 'CPU', 'Dell', 'Optiplex 3080', 'ABC123', 'disponible', 'Si', 1, 'admin'),
                ('BOG-MON-001', 'Monitor', 'Samsung', 'S24R650', 'DEF456', 'disponible', 'Si', 1, 'admin'),
                ('MED-CPU-001', 'CPU', 'HP', 'ProDesk 400', 'GHI789', 'disponible', 'Si', 3, 'admin')
            """)

            conn.commit()
            print("✅ Datos de ejemplo insertados")

        except Exception as e:
            print(f"❌ Error insertando datos de ejemplo: {e}")
        finally:
            conn.close()

def main():
    """Función principal"""
    print("🔄 WORKMANAGER ERP - Reset de Base de Datos")
    print("=" * 50)

    # Confirmar acción
    if not confirm_reset():
        print("❌ Operación cancelada por el usuario")
        return

    # Crear backup
    backup_file = backup_database()

    # Eliminar base de datos
    if not remove_database():
        print("❌ Error eliminando base de datos")
        return

    # Recrear base de datos
    if not recreate_database():
        print("❌ Error recreando base de datos")
        return

    # Poblar con datos de ejemplo
    populate_sample_data()

    print("\n" + "=" * 50)
    print("🎉 ¡Reset completado exitosamente!")
    if backup_file:
        print(f"📦 Backup guardado en: {backup_file}")
    print("\n📋 El sistema está listo para usar.")

if __name__ == "__main__":
    main()
