# -*- coding: utf-8 -*-
import json
import sqlite3
import os
import sys

def table_has_column(cursor, table_name, column_name):
    """Valida si una columna existe en la tabla, usando PRAGMA table_info."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return any(col[1] == column_name for col in cursor.fetchall())

def get_project_root():
    """Navega hacia arriba desde la ubicación del script para encontrar la raíz del proyecto."""
    # La ruta actual del script es .../scripts/inventario
    # Necesitamos subir dos niveles para llegar a la raíz del proyecto.
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def main():
    """
    Función principal para importar datos de inventario desde un JSON a la base de datos SQLite.
    """
    print("--- INICIANDO IMPORTADOR MASIVO WORKMANAGER ---")
    
    project_root = get_project_root()
    db_path = os.path.join(project_root, 'workmanager_erp.db')
    json_path = os.path.join(project_root, 'sample_data.json')

    print(f"[INFO] Raíz del proyecto detectada en: {project_root}")
    print(f"[INFO] Buscando base de datos en: {db_path}")
    print(f"[INFO] Buscando archivo de datos en: {json_path}")

    # --- Verificación de archivos ---
    if not os.path.exists(db_path):
        print(f"[ERROR] La base de datos '{db_path}' no existe.")
        print("[ERROR] Por favor, ejecuta primero la opción '1. Crear/Inicializar Base de Datos' desde el menú.")
        sys.exit(1)

    if not os.path.exists(json_path):
        print(f"[ERROR] El archivo de datos '{json_path}' no fue encontrado.")
        sys.exit(1)

    # --- Carga de datos desde JSON ---
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("[OK] Archivo JSON cargado correctamente.")
    except json.JSONDecodeError as e:
        print(f"[ERROR] El archivo JSON está mal formado: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Ocurrió un error al leer el archivo JSON: {e}")
        sys.exit(1)

    conn = None
    try:
        # --- Conexión e inserción en la BD ---
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"[OK] Conexión exitosa a la base de datos: {db_path}")


        # --- Importar Equipos Individuales ---
        equipos_individuales = data.get('equipos_individuales', [])
        if 'inventario_general' in data and 'individuales' in data['inventario_general']:
            equipos_individuales.extend(data['inventario_general']['individuales'])
        
        if equipos_individuales:
            sedes_a_insertar = set()
            empleados_a_insertar = set()
            print(f"\n[INFO] Importando {len(equipos_individuales)} registro(s) a 'equipos_individuales'...")
            for item in equipos_individuales:
                # Usamos INSERT OR IGNORE para evitar fallos si el codigo_barras_individual ya existe.
                # Ahora incluimos todos los campos relevantes del JSON.
                cursor.execute("""
                    INSERT OR IGNORE INTO equipos_individuales 
                    (codigo_barras_individual, entrada_oc_compra, cargado_nit, ciudad, tecnologia, serial, modelo, 
                     placa, marca, procesador, arch_ram, cantidad_ram, tipo_disco, espacio_disco, so, estado, 
                     asignado_nuevo, fecha, fecha_llegada, area, marca_monitor, modelo_monitor, serial_monitor, 
                     placa_monitor, proveedor, oc, observaciones, disponible, sede_id, creador_registro)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get('codigo_barras_individual'), item.get('entrada_oc_compra'), item.get('cargado_nit'), 
                    item.get('ciudad'), item.get('tecnologia'), item.get('serial'), item.get('modelo'), 
                    item.get('placa'), item.get('marca'), item.get('procesador'), item.get('arch_ram'), 
                    item.get('cantidad_ram'), item.get('tipo_disco'), item.get('espacio_disco'), item.get('so'), 
                    item.get('estado'), item.get('asignado_nuevo'), item.get('fecha'), item.get('fecha_llegada'), 
                    item.get('area'), item.get('marca_monitor'), item.get('modelo_monitor'), item.get('serial_monitor'), 
                    item.get('placa_monitor'), item.get('proveedor'), item.get('oc'), item.get('observaciones'), 
                    item.get('disponible'), item.get('sede_id'), item.get('creador_registro', 'AUTO_IMPORT')
                ))
                # Recolectar datos para otras tablas
                if item.get('sede_id'):
                    sedes_a_insertar.add((item['sede_id'], item.get('ciudad')))
                if item.get('asignado_nuevo'):
                    empleados_a_insertar.add((item['asignado_nuevo'], item.get('area')))
            print("[OK] Finalizada la importación de equipos individuales.")

        # --- Importar Equipos Agrupados ---
        equipos_agrupados = data.get('equipos_agrupados', [])
        if 'inventario_general' in data and 'agrupados' in data['inventario_general']:
            equipos_agrupados.extend(data['inventario_general']['agrupados'])

        if equipos_agrupados:
            # Reiniciamos los sets si no se procesaron individuales
            sedes_a_insertar = sedes_a_insertar if 'sedes_a_insertar' in locals() else set()
            empleados_a_insertar = empleados_a_insertar if 'empleados_a_insertar' in locals() else set()
            print(f"\n[INFO] Importando {len(equipos_agrupados)} registro(s) a 'equipos_agrupados'...")
            for item in equipos_agrupados:
                cursor.execute("""
                    INSERT OR IGNORE INTO equipos_agrupados
                    (codigo_barras_unificado, descripcion_general, estado_general, asignado_actual, sede_id, observaciones, creador_registro)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.get('codigo_barras_unificado'), item.get('descripcion_general'), item.get('estado_general'),
                    item.get('asignado_actual'), item.get('sede_id'), item.get('observaciones'), item.get('creador_registro', 'AUTO_IMPORT')
                ))
                # Recolectar datos para otras tablas
                if item.get('sede_id'):
                    # No tenemos ciudad en agrupados, así que pasamos None
                    sedes_a_insertar.add((item['sede_id'], None))
                if item.get('asignado_actual'):
                    # No tenemos área en agrupados, así que pasamos None
                    empleados_a_insertar.add((item['asignado_actual'], None))
            print("[OK] Finalizada la importación de equipos agrupados.")

        # --- Importar Sedes (si se recolectaron) ---
        if sedes_a_insertar:
            print(f"\n[INFO] Importando {len(sedes_a_insertar)} registro(s) a 'sedes'...")
            # Usamos un diccionario para quedarnos con la primera ciudad encontrada para una sede_id
            sedes_unicas = {sede_id: ciudad for sede_id, ciudad in sedes_a_insertar if ciudad}
            for sede_id, ciudad in sedes_a_insertar:
                if sede_id not in sedes_unicas:
                    sedes_unicas[sede_id] = ciudad
            
            for sede_id, ciudad in sedes_unicas.items():
                nombre_sede = f"Sede {ciudad}" if ciudad else f"Sede ID {sede_id}"
                cursor.execute("INSERT OR IGNORE INTO sedes (id, nombre, ciudad) VALUES (?, ?, ?)", (sede_id, nombre_sede, ciudad))
            print("[OK] Finalizada la importación de sedes.")

        # --- Importar Empleados (si se recolectaron) ---
        if empleados_a_insertar:
            print(f"\n[INFO] Importando {len(empleados_a_insertar)} registro(s) a 'empleados'...")
            has_area = table_has_column(cursor, "empleados", "area")
            for nombre, area in empleados_a_insertar:
                # Como no tenemos ID, dejamos que se autoincremente. El nombre será la clave.
                if has_area:
                    cursor.execute("INSERT OR IGNORE INTO empleados (nombre, area) VALUES (?, ?)", (nombre, area))
                else:
                    cursor.execute("INSERT OR IGNORE INTO empleados (nombre) VALUES (?)", (nombre,))
            print("[OK] Finalizada la importación de empleados.")

        conn.commit()
        print("\n[SUCCESS] Todos los datos han sido guardados en la base de datos.")

    except sqlite3.Error as e:
        print(f"\n[FATAL] Error de base de datos: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
        print("\n--- IMPORTADOR MASIVO FINALIZADO ---")

if __name__ == '__main__':
    main()
