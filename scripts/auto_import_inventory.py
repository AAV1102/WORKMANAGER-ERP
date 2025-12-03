#!/usr/bin/env python3
"""
Automated Inventory Import Script for WORKMANAGER ERP
This script automatically imports inventory data and updates all related tabs
"""

import sqlite3
import pandas as pd
import os
import sys
import json
from datetime import datetime
import logging
import os

# Configure logging
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, 'auto_import.log')

logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AutoInventoryImporter:
    def __init__(self, db_path='workmanager_erp.db'):
        self.db_path = db_path
        self.stats = {
            'equipos_agrupados': 0,
            'equipos_individuales': 0,
            'inventario_general': 0,
            'equipos_asignados': 0,
            'equipos_baja': 0,
            'tandas_nuevas': 0
        }

    def connect_db(self):
        """Connect to the database"""
        return sqlite3.connect(self.db_path)

    def import_equipos_agrupados(self, data):
        """Import equipos agrupados data"""
        conn = self.connect_db()
        cursor = conn.cursor()

        for item in data:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO equipos_agrupados
                    (codigo_barras_unificado, nit, sede_id, asignado_anterior,
                     asignado_actual, descripcion_general, estado_general,
                     creador_registro, fecha_creacion, trazabilidad_soporte,
                     documentos_entrega, observaciones)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.get('codigo_barras_unificado'),
                    item.get('nit', '901.234.567-8'),
                    item.get('sede_id'),
                    item.get('asignado_anterior'),
                    item.get('asignado_actual'),
                    item.get('descripcion_general'),
                    item.get('estado_general', 'disponible'),
                    item.get('creador_registro', 'AUTO_IMPORT'),
                    item.get('fecha_creacion', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    item.get('trazabilidad_soporte'),
                    item.get('documentos_entrega'),
                    item.get('observaciones')
                ))
                self.stats['equipos_agrupados'] += 1
            except Exception as e:
                logging.error(f"Error importing equipo agrupado: {e}")

        conn.commit()
        conn.close()

    def import_equipos_individuales(self, data):
        """Import equipos individuales data"""
        conn = self.connect_db()
        cursor = conn.cursor()

        for item in data:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO equipos_individuales
                    (codigo_barras_individual, entrada_oc_compra, cargado_nit,
                     ciudad, tecnologia, serial, modelo, anterior_asignado, placa,
                     marca, procesador, arch_ram, cantidad_ram, tipo_disco,
                     espacio_disco, so, estado, asignado_nuevo, fecha, fecha_llegada,
                     area, marca_monitor, modelo_monitor, serial_monitor,
                     placa_monitor, proveedor, oc, observaciones, disponible, sede_id,
                     creador_registro, fecha_creacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.get('codigo_barras_individual'),
                    item.get('entrada_oc_compra'),
                    item.get('cargado_nit'),
                    item.get('ciudad'),
                    item.get('tecnologia'),
                    item.get('serial'),
                    item.get('modelo'),
                    item.get('anterior_asignado'),
                    item.get('placa'),
                    item.get('marca'),
                    item.get('procesador'),
                    item.get('arch_ram'),
                    item.get('cantidad_ram'),
                    item.get('tipo_disco'),
                    item.get('espacio_disco'),
                    item.get('so'),
                    item.get('estado', 'disponible'),
                    item.get('asignado_nuevo'),
                    item.get('fecha'),
                    item.get('fecha_llegada'),
                    item.get('area'),
                    item.get('marca_monitor'),
                    item.get('modelo_monitor'),
                    item.get('serial_monitor'),
                    item.get('placa_monitor'),
                    item.get('proveedor'),
                    item.get('oc'),
                    item.get('observaciones'),
                    item.get('disponible', 'Si'),
                    item.get('sede_id'),
                    item.get('creador_registro', 'AUTO_IMPORT'),
                    item.get('fecha_creacion', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                ))
                self.stats['equipos_individuales'] += 1
            except Exception as e:
                logging.error(f"Error importing equipo individual: {e}")

        conn.commit()
        conn.close()

    def import_inventario_general(self, data):
        """Import inventario general data"""
        # This could be a combination of both types or a separate table
        # For now, we'll treat it as updating both tables
        self.import_equipos_agrupados(data.get('agrupados', []))
        self.import_equipos_individuales(data.get('individuales', []))
        self.stats['inventario_general'] = self.stats['equipos_agrupados'] + self.stats['equipos_individuales']

    def import_equipos_asignados(self, data):
        """Import equipos asignados data"""
        conn = self.connect_db()
        cursor = conn.cursor()

        for item in data:
            try:
                # Update the assigned status in equipos_individuales or equipos_agrupados
                cursor.execute('''
                    UPDATE equipos_individuales
                    SET asignado_nuevo = ?, estado = 'asignado'
                    WHERE codigo_barras_individual = ?
                ''', (item.get('asignado_a'), item.get('codigo')))

                cursor.execute('''
                    UPDATE equipos_agrupados
                    SET asignado_actual = ?, estado_general = 'asignado'
                    WHERE codigo_barras_unificado = ?
                ''', (item.get('asignado_a'), item.get('codigo')))

                self.stats['equipos_asignados'] += 1
            except Exception as e:
                logging.error(f"Error importing equipo asignado: {e}")

        conn.commit()
        conn.close()

    def import_equipos_baja(self, data):
        """Import equipos dados de baja"""
        conn = self.connect_db()
        cursor = conn.cursor()

        for item in data:
            try:
                cursor.execute('''
                    INSERT INTO inventario_bajas
                    (equipo_id, tipo_inventario, motivo_baja, responsable_baja,
                     documentos_soporte, fotografias_soporte, observaciones)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.get('equipo_id'),
                    item.get('tipo_inventario'),
                    item.get('motivo_baja'),
                    item.get('responsable_baja'),
                    item.get('documentos_soporte'),
                    item.get('fotografias_soporte'),
                    item.get('observaciones')
                ))

                # Update status to baja
                cursor.execute('''
                    UPDATE equipos_individuales SET estado = 'baja'
                    WHERE id = ?
                ''', (item.get('equipo_id'),))

                cursor.execute('''
                    UPDATE equipos_agrupados SET estado_general = 'baja'
                    WHERE id = ?
                ''', (item.get('equipo_id'),))

                self.stats['equipos_baja'] += 1
            except Exception as e:
                logging.error(f"Error importing equipo baja: {e}")

        conn.commit()
        conn.close()

    def import_tandas_nuevas(self, data):
        """Import tandas nuevas data"""
        conn = self.connect_db()
        cursor = conn.cursor()

        for item in data:
            try:
                cursor.execute('''
                    INSERT INTO tandas_equipos_nuevos
                    (numero_tanda, descripcion, cantidad_equipos, proveedor,
                     valor_total, observaciones)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    item.get('numero_tanda'),
                    item.get('descripcion'),
                    item.get('cantidad_equipos'),
                    item.get('proveedor'),
                    item.get('valor_total'),
                    item.get('observaciones')
                ))
                self.stats['tandas_nuevas'] += 1
            except Exception as e:
                logging.error(f"Error importing tanda nueva: {e}")

        conn.commit()
        conn.close()

    def import_from_json(self, json_file):
        """Import data from JSON file"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logging.info(f"Starting auto import from {json_file}")

            if 'equipos_agrupados' in data:
                self.import_equipos_agrupados(data['equipos_agrupados'])
            if 'equipos_individuales' in data:
                self.import_equipos_individuales(data['equipos_individuales'])
            if 'inventario_general' in data:
                self.import_inventario_general(data['inventario_general'])
            if 'equipos_asignados' in data:
                self.import_equipos_asignados(data['equipos_asignados'])
            if 'equipos_baja' in data:
                self.import_equipos_baja(data['equipos_baja'])
            if 'tandas_nuevas' in data:
                self.import_tandas_nuevas(data['tandas_nuevas'])

            logging.info(f"Auto import completed. Stats: {self.stats}")
            return self.stats

        except Exception as e:
            logging.error(f"Error in auto import: {e}")
            return None

    def import_from_csv(self, csv_file, data_type):
        """Import data from CSV file"""
        try:
            df = pd.read_csv(csv_file)
            data = df.to_dict('records')

            if data_type == 'equipos_agrupados':
                self.import_equipos_agrupados(data)
            elif data_type == 'equipos_individuales':
                self.import_equipos_individuales(data)
            elif data_type == 'equipos_asignados':
                self.import_equipos_asignados(data)
            elif data_type == 'equipos_baja':
                self.import_equipos_baja(data)
            elif data_type == 'tandas_nuevas':
                self.import_tandas_nuevas(data)

            return self.stats

        except Exception as e:
            logging.error(f"Error importing from CSV: {e}")
            return None

def main():
    importer = AutoInventoryImporter()

    if len(sys.argv) < 2:
        print("Usage: python auto_import_inventory.py <json_file>")
        sys.exit(1)

    json_file = sys.argv[1]

    if not os.path.exists(json_file):
        print(f"File {json_file} not found")
        sys.exit(1)

    result = importer.import_from_json(json_file)

    if result:
        print("Import completed successfully!")
        print(json.dumps(result, indent=2))
    else:
        print("Import failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
