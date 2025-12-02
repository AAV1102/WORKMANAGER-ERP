#!/usr/bin/env python3
"""
Script para poblar empleados desde inventario tecnológico y licencias
WORKMANAGER ERP
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = 'workmanager_erp.db'

def get_db_connection():
    """Conecta a la base de datos"""
    return sqlite3.connect(DB_PATH)

def extract_employees_from_inventory():
    """Extrae empleados desde equipos individuales y agrupados"""
    conn = get_db_connection()
    cur = conn.cursor()

    employees_data = []

    try:
        # Extraer de equipos individuales
        cur.execute("""
            SELECT DISTINCT
                asignado_nuevo as nombre_completo,
                ciudad as sede,
                'inventario_individual' as fuente,
                COUNT(*) as equipos_asignados
            FROM equipos_individuales
            WHERE asignado_nuevo IS NOT NULL
                AND asignado_nuevo != ''
                AND asignado_nuevo != 'No asignado'
            GROUP BY asignado_nuevo, ciudad
        """)

        for row in cur.fetchall():
            employees_data.append({
                'nombre_completo': row['nombre_completo'].strip(),
                'sede': row['sede'] or 'Bogotá',
                'fuente': row['fuente'],
                'equipos_asignados': row['equipos_asignados']
            })

        # Extraer de equipos agrupados
        cur.execute("""
            SELECT DISTINCT
                asignado_actual as nombre_completo,
                (SELECT ciudad FROM sedes WHERE id = sede_id) as sede,
                'inventario_agrupado' as fuente,
                1 as equipos_asignados
            FROM equipos_agrupados
            WHERE asignado_actual IS NOT NULL
                AND asignado_actual != ''
                AND asignado_actual != 'No asignado'
        """)

        for row in cur.fetchall():
            employees_data.append({
                'nombre_completo': row['nombre_completo'].strip(),
                'sede': row['sede'] or 'Bogotá',
                'fuente': row['fuente'],
                'equipos_asignados': row['equipos_asignados']
            })

    finally:
        conn.close()

    return employees_data

def extract_employees_from_licenses():
    """Extrae empleados desde licencias de Office 365"""
    conn = get_db_connection()
    cur = conn.cursor()

    employees_data = []

    try:
        cur.execute("""
            SELECT DISTINCT
                usuario_asignado as nombre_completo,
                cedula_usuario,
                (SELECT nombre FROM sedes WHERE id = sede_id) as sede,
                email,
                'licencias_office365' as fuente,
                1 as licencias_asignadas
            FROM licencias_office365
            WHERE usuario_asignado IS NOT NULL
                AND usuario_asignado != ''
                AND estado = 'activa'
        """)

        for row in cur.fetchall():
            employees_data.append({
                'nombre_completo': row['nombre_completo'].strip(),
                'cedula': row['cedula_usuario'],
                'sede': row['sede'] or 'Bogotá',
                'email': row['email'],
                'fuente': row['fuente'],
                'licencias_asignadas': row['licencias_asignadas']
            })

    finally:
        conn.close()

    return employees_data

def merge_employee_data(inventory_data, licenses_data):
    """Fusiona datos de empleados eliminando duplicados"""
    merged = {}

    # Procesar datos de inventario
    for emp in inventory_data:
        key = emp['nombre_completo'].lower().strip()
        if key not in merged:
            merged[key] = {
                'nombre_completo': emp['nombre_completo'],
                'sede': emp['sede'],
                'fuentes': [emp['fuente']],
                'equipos_asignados': emp.get('equipos_asignados', 0),
                'licencias_asignadas': 0,
                'cedula': None,
                'email': None
            }
        else:
            if emp['fuente'] not in merged[key]['fuentes']:
                merged[key]['fuentes'].append(emp['fuente'])
            merged[key]['equipos_asignados'] += emp.get('equipos_asignados', 0)

    # Procesar datos de licencias
    for emp in licenses_data:
        key = emp['nombre_completo'].lower().strip()
        if key not in merged:
            merged[key] = {
                'nombre_completo': emp['nombre_completo'],
                'sede': emp['sede'],
                'fuentes': [emp['fuente']],
                'equipos_asignados': 0,
                'licencias_asignadas': emp.get('licencias_asignadas', 0),
                'cedula': emp.get('cedula'),
                'email': emp.get('email')
            }
        else:
            if emp['fuente'] not in merged[key]['fuentes']:
                merged[key]['fuentes'].append(emp['fuente'])
            merged[key]['licencias_asignadas'] += emp.get('licencias_asignadas', 0)
            # Actualizar cédula y email si no existen
            if not merged[key]['cedula'] and emp.get('cedula'):
                merged[key]['cedula'] = emp['cedula']
            if not merged[key]['email'] and emp.get('email'):
                merged[key]['email'] = emp['email']

    return list(merged.values())

def create_employees(employees_data, create_mode='preview'):
    """Crea empleados en la base de datos"""
    conn = get_db_connection()
    cur = conn.cursor()

    created = 0
    skipped = 0
    errors = 0

    try:
        for emp in employees_data:
            try:
                # Verificar si ya existe
                cur.execute("SELECT id FROM empleados WHERE LOWER(nombre) = LOWER(?)",
                          (emp['nombre_completo'],))
                existing = cur.fetchone()

                if existing:
                    print(f"⚠️  Empleado ya existe: {emp['nombre_completo']}")
                    skipped += 1
                    continue

                if create_mode == 'create':
                    # Separar nombre y apellido
                    nombre_completo = emp['nombre_completo']
                    partes = nombre_completo.split(' ', 1)
                    nombre = partes[0]
                    apellido = partes[1] if len(partes) > 1 else ''

                    # Obtener sede_id
                    cur.execute("SELECT id FROM sedes WHERE LOWER(nombre) LIKE LOWER(?)",
                              (f"%{emp['sede']}%",))
                    sede_row = cur.fetchone()
                    sede_id = sede_row['id'] if sede_row else 1  # Default a primera sede

                    # Insertar empleado
                    cur.execute("""
                        INSERT INTO empleados (
                            nombre, apellido, cedula, email, sede_id, estado,
                            observaciones, fecha_ingreso
                        ) VALUES (?, ?, ?, ?, ?, 'activo', ?, ?)
                    """, (
                        nombre, apellido, emp.get('cedula'), emp.get('email'),
                        sede_id, f"Creado desde: {', '.join(emp['fuentes'])}",
                        datetime.now().strftime('%Y-%m-%d')
                    ))

                    print(f"✅ Empleado creado: {emp['nombre_completo']}")
                    created += 1

                else:  # preview mode
                    print(f"👤 {emp['nombre_completo']} - Fuentes: {', '.join(emp['fuentes'])} - Equipos: {emp['equipos_asignados']} - Licencias: {emp['licencias_asignadas']}")

            except Exception as e:
                print(f"❌ Error procesando {emp['nombre_completo']}: {e}")
                errors += 1

        if create_mode == 'create':
            conn.commit()

    finally:
        conn.close()

    return created, skipped, errors

def main():
    """Función principal"""
    print("👥 WORKMANAGER ERP - Poblar Empleados desde Inventario")
    print("=" * 60)

    # Extraer datos
    print("\n🔍 Extrayendo empleados desde inventario...")
    inventory_data = extract_employees_from_inventory()
    print(f"📊 Encontrados {len(inventory_data)} empleados en inventario")

    print("\n🔍 Extrayendo empleados desde licencias...")
    licenses_data = extract_employees_from_licenses()
    print(f"📊 Encontrados {len(licenses_data)} empleados en licencias")

    # Fusionar datos
    print("\n🔄 Fusionando datos...")
    merged_data = merge_employee_data(inventory_data, licenses_data)
    print(f"📊 Total empleados únicos: {len(merged_data)}")

    # Mostrar preview
    print("\n👀 PREVIEW DE EMPLEADOS A CREAR:")
    print("-" * 60)
    created, skipped, errors = create_employees(merged_data, create_mode='preview')

    # Preguntar si crear
    print(f"\n📋 Resumen:")
    print(f"- Total empleados a procesar: {len(merged_data)}")
    print(f"- Se crearían: {len(merged_data)}")
    print(f"- Posibles duplicados: {skipped}")

    if input("\n¿Crear empleados en la base de datos? (s/n): ").lower() == 's':
        print("\n🚀 Creando empleados...")
        created, skipped, errors = create_employees(merged_data, create_mode='create')

        print("
✅ Proceso completado:"        print(f"- Creados: {created}")
        print(f"- Omitidos: {skipped}")
        print(f"- Errores: {errors}")

        print("\n💡 RECUERDA:")
        print("- Revisar y completar la información faltante de los empleados creados")
        print("- Asignar credenciales de acceso si es necesario")
        print("- Verificar la información de contacto y cargos")
    else:
        print("\n❌ Operación cancelada")

if __name__ == "__main__":
    main()
