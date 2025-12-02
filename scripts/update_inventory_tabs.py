#!/usr/bin/env python3
"""
Script para actualizar las tabs de inventario (Asignados, Bajas, Tandas)
WORKMANAGER ERP
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = 'workmanager_erp.db'

def get_db_connection():
    """Conecta a la base de datos"""
    return sqlite3.connect(DB_PATH)

def update_inventory_tabs():
    """Actualiza las consultas y datos para las tabs de inventario"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        print("🔄 Actualizando tabs de inventario...")

        # 1. Tab "Asignados" - Equipos asignados a empleados
        print("📋 Actualizando tab 'Asignados'...")

        # Crear vista para equipos asignados
        cur.execute("""
            CREATE VIEW IF NOT EXISTS equipos_asignados AS
            SELECT
                'individual' as tipo,
                ei.id,
                ei.codigo_barras_individual as codigo,
                ei.serial,
                ei.marca,
                ei.modelo,
                ei.asignado_nuevo as asignado_a,
                ei.fecha as fecha_asignacion,
                s.nombre as sede,
                ei.estado,
                e.cedula as cedula_empleado,
                e.cargo,
                e.departamento
            FROM equipos_individuales ei
            LEFT JOIN sedes s ON s.id = ei.sede_id
            LEFT JOIN empleados e ON LOWER(e.nombre || ' ' || IFNULL(e.apellido, '')) = LOWER(ei.asignado_nuevo)
            WHERE ei.asignado_nuevo IS NOT NULL
                AND ei.asignado_nuevo != ''
                AND ei.asignado_nuevo != 'No asignado'
                AND LOWER(ei.estado) = 'asignado'

            UNION ALL

            SELECT
                'agrupado' as tipo,
                ea.id,
                ea.codigo_barras_unificado as codigo,
                '' as serial,
                '' as marca,
                ea.descripcion_general as modelo,
                ea.asignado_actual as asignado_a,
                ea.fecha_creacion as fecha_asignacion,
                s.nombre as sede,
                ea.estado_general as estado,
                e.cedula as cedula_empleado,
                e.cargo,
                e.departamento
            FROM equipos_agrupados ea
            LEFT JOIN sedes s ON s.id = ea.sede_id
            LEFT JOIN empleados e ON LOWER(e.nombre || ' ' || IFNULL(e.apellido, '')) = LOWER(ea.asignado_actual)
            WHERE ea.asignado_actual IS NOT NULL
                AND ea.asignado_actual != ''
                AND ea.asignado_actual != 'No asignado'
                AND LOWER(ea.estado_general) = 'asignado'
        """)

        # 2. Tab "Bajas" - Equipos dados de baja
        print("📋 Actualizando tab 'Bajas'...")

        # Crear vista para equipos dados de baja
        cur.execute("""
            CREATE VIEW IF NOT EXISTS equipos_bajas AS
            SELECT
                'individual' as tipo,
                ei.id,
                ei.codigo_barras_individual as codigo,
                ei.serial,
                ei.marca,
                ei.modelo,
                ei.observaciones as motivo_baja,
                ei.fecha_creacion as fecha_baja,
                s.nombre as sede,
                'Dado de baja' as estado,
                e.nombre || ' ' || IFNULL(e.apellido, '') as dado_de_baja_por
            FROM equipos_individuales ei
            LEFT JOIN sedes s ON s.id = ei.sede_id
            LEFT JOIN empleados e ON LOWER(e.nombre || ' ' || IFNULL(e.apellido, '')) = LOWER(ei.asignado_nuevo)
            WHERE LOWER(ei.estado) = 'baja'

            UNION ALL

            SELECT
                'agrupado' as tipo,
                ea.id,
                ea.codigo_barras_unificado as codigo,
                '' as serial,
                '' as marca,
                ea.descripcion_general as modelo,
                ea.observaciones as motivo_baja,
                ea.fecha_creacion as fecha_baja,
                s.nombre as sede,
                'Dado de baja' as estado,
                ea.creador_registro as dado_de_baja_por
            FROM equipos_agrupados ea
            LEFT JOIN sedes s ON s.id = ea.sede_id
            WHERE LOWER(ea.estado_general) = 'baja'
        """)

        # 3. Tab "Tandas" - Equipos nuevos en tandas
        print("📋 Actualizando tab 'Tandas'...")

        # Asegurar que existe la tabla tandas_equipos_nuevos
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tandas_equipos_nuevos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_tanda TEXT UNIQUE,
                descripcion TEXT,
                fecha_ingreso TEXT DEFAULT CURRENT_TIMESTAMP,
                cantidad_equipos INTEGER DEFAULT 0,
                proveedor TEXT,
                valor_total REAL DEFAULT 0,
                estado TEXT DEFAULT 'en_proceso',
                observaciones TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insertar datos de ejemplo si no existen
        cur.execute("SELECT COUNT(*) FROM tandas_equipos_nuevos")
        if cur.fetchone()[0] == 0:
            tandas_ejemplo = [
                ('TANDA-2024-001', 'Equipos Dell Optiplex 3080', 10, 'Dell Technologies', 15000000, 'Equipos nuevos para reemplazo'),
                ('TANDA-2024-002', 'Monitores Samsung 24"', 15, 'Samsung Electronics', 7500000, 'Monitores para nueva sede'),
                ('TANDA-2024-003', 'Laptops HP ProBook', 8, 'HP Inc.', 24000000, 'Laptops para ejecutivos')
            ]

            cur.executemany("""
                INSERT INTO tandas_equipos_nuevos
                (numero_tanda, descripcion, cantidad_equipos, proveedor, valor_total, observaciones)
                VALUES (?, ?, ?, ?, ?, ?)
            """, tandas_ejemplo)

        # 4. Actualizar estadísticas de inventario
        print("📊 Actualizando estadísticas...")

        # Estadísticas por estado
        cur.execute("""
            CREATE VIEW IF NOT EXISTS inventario_estadisticas AS
            SELECT
                'disponible' as estado,
                COUNT(*) as cantidad
            FROM equipos_individuales
            WHERE LOWER(estado) = 'disponible'
                AND LOWER(disponible) = 'si'

            UNION ALL

            SELECT
                'asignado' as estado,
                COUNT(*) as cantidad
            FROM equipos_individuales
            WHERE LOWER(estado) = 'asignado'

            UNION ALL

            SELECT
                'baja' as estado,
                COUNT(*) as cantidad
            FROM equipos_individuales
            WHERE LOWER(estado) = 'baja'

            UNION ALL

            SELECT
                'mantenimiento' as estado,
                COUNT(*) as cantidad
            FROM equipos_individuales
            WHERE LOWER(estado) = 'mantenimiento'
        """)

        conn.commit()
        print("✅ Tabs de inventario actualizadas correctamente")

    except Exception as e:
        print(f"❌ Error actualizando tabs: {e}")
        conn.rollback()
    finally:
        conn.close()

def update_inventory_template():
    """Actualiza el template de inventarios para incluir las nuevas tabs"""
    template_path = 'templates/inventarios.html'

    if not os.path.exists(template_path):
        print(f"❌ Template no encontrado: {template_path}")
        return

    # Leer template actual
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verificar si ya tiene las tabs
    if 'id="asignados"' in content and 'id="bajas"' in content and 'id="tandas"' in content:
        print("✅ Template ya tiene las tabs actualizadas")
        return

    # Aquí iría la lógica para actualizar el template
    # Por simplicidad, solo notificamos que necesita actualización manual
    print("⚠️  El template necesita actualización manual")
    print("   Agregar las tabs 'Asignados', 'Bajas' y 'Tandas' al template inventarios.html")

def main():
    """Función principal"""
    print("🔄 WORKMANAGER ERP - Actualizar Tabs de Inventario")
    print("=" * 55)

    update_inventory_tabs()
    update_inventory_template()

    print("\n✅ Actualización completada")
    print("\n📋 Las tabs ahora incluyen:")
    print("- Asignados: Equipos asignados a empleados")
    print("- Bajas: Equipos dados de baja")
    print("- Tandas: Nuevos equipos en tandas")
    print("\n💡 Recuerda actualizar el template HTML si es necesario")

if __name__ == "__main__":
    main()
