#!/usr/bin/env python3
"""
Parser for disorganized inventory files (CSV/XLSX) with dynamic header detection
WORKMANAGER ERP
"""

import pandas as pd
import os
import json
import logging
from typing import Dict, List, Any, Optional
import re

# Configure logging
logging.basicConfig(
    filename='logs/inventory_parser.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DisorganizedInventoryParser:
    def __init__(self):
        self.inventory_types = {
            'INVENTARIO BODEGA MEDELLIN': {
                'PC:': ['SERIAL', 'MODELO', 'MARCA', 'PROCESADOR', 'RAM', 'ALMACENAMIENTO', 'ESTADO', 'DISPOSITIVO', 'SEDE UBICACIÓN'],
                'POS:': ['MODELO', 'SERIAL', 'MARCA', 'ESTADO', 'DISPOSITIVO', 'SEDE'],
                'SWITCHES:': ['SERIAL', 'MODELO', 'MARCA', 'DISPOSITIVO', 'ESTADO', 'SEDE UBICACIÓN'],
                'CISCO:': ['SERIAL', 'MARCA', 'MODELO', 'ESTADO', 'DISPOSITIVO', 'SEDE'],
                'MONITOR:': ['SERIAL', 'MARCA', 'MODELO', 'ESTADO', 'DISPOSITIVO', 'SEDE UBICACIÓN'],
                'CAMARAS PC:': ['SERIAL', 'MARCA', 'MODELO', 'ESTADO', 'SEDE'],
                'IMPRESORA:': ['SERIAL', 'MODELO', 'MARCA', 'DISPOSITIVO', 'SEDE UBICACIÓN'],
                'TELEFONOS:': ['SERIAL', 'MARCA', 'DISPOSITIVO', 'SEDE UBICACIÓN'],
                'OTROS:': ['TIPO DISPOSITIVO', 'CANTIDAD']
            },
            'INVENTARIO SEDES:': {
                'CARTAGENA:': ['ENTRADA OC COMPRA', 'ENVIADO /CARGADO', 'CIUDAD', 'TECNOLOGIA', 'SERIAL', 'MODELO', 'ANTERIOR ASIGNADO', 'PLACA', 'MARCA', 'PROCESADOR', 'ARQUI RAM', 'CANTIDAD RAM', 'TIPO DE DISCO', 'ESPACIO DISCO', 'SO', 'Estado', 'ASIGNADO NUEVO', 'FECHA', 'FECHA DE LLEGADA', 'AREA', 'MARCA DE  MONITOR', 'MODELO DE MONITOR', 'SERIAL2', 'PLACA DE MONITOR', 'PROVEEDOR ', 'OC', 'OBSERVACIONES', 'DISPONIBLE'],
                'MONTERIA:': ['Sede', 'Tipo de dispositivo', 'Serial o Mac', 'Modelo', 'Marca', 'Procesador', 'Tipo de ram', 'Cantidad de ram', 'Tipo de disco', 'Espacio de disco', 'Estado', 'Asignado a', 'Fecha LLegada', 'Area o Ciudad', 'Codigo interno'],
                'PASTO:': ['ITEM', 'DESCRIPCION DE LOS ACTIVOS', 'MODELO', 'SERIE No.', 'MARCA', 'PLACA No.', 'CANTIDAD ', 'UNIDAD DE MEDIDA', 'VALOR', 'ESTADO ACTUAL', 'OBSERVACIÓN', 'CONSULTORIO'],
                'informe_activos_tecnologia': ['NIT', 'Sede', 'Tipo de dispositivo', 'Serial o Mac', 'Modelo', 'IMEI', 'Marca', 'Procesador', 'Tipo de ram', 'Cantidad de ram', 'Tipo de disco', 'Espacio de disco', 'Teclado', 'Mouse', 'Estado', 'Asignado a', 'Area Asignado', 'Cargo Asignado', 'Observaciones', 'Hostname', 'Fecha de creacion', 'Fecha de compra']
            },
            'INVENTARIO GENERAL': {
                'INVENTARIO_ACTUALIZADO': ['ENTRADA OC COMPRA', 'ENVIADO /CARGADO', 'CIUDAD', 'TECNOLOGIA', 'SERIAL', 'MODELO', 'ANTERIOR ASIGNADO', 'PLACA', 'MARCA', 'PROCESADOR', 'ARQUI RAM', 'CANTIDAD RAM', 'TIPO DE DISCO', 'ESPACIO DISCO', 'SO', 'Estado', 'ASIGNADO NUEVO', 'FECHA', 'FECHA DE LLEGADA', 'AREA', 'MARCA DE  MONITOR', 'MODELO DE MONITOR', 'SERIAL', 'PLACA DE MONITOR', 'PROVEEDOR ', 'OC', 'OBSERVACIONES', 'DISPONIBLE'],
                'EQUIPO_ENTREGADO': ['NOMBRE', 'CIUDAD', 'PLACA', 'SERIAL', 'PESTAÑA ', 'FECHA DE ENVIO', 'GUIA'],
                'ACCESORIOS_ASIGNADOS': ['NOMBRE DE LA PARTE', 'CANTIDAD', 'ASIGNADO', 'AREA', 'PLACA', 'FECHA'],
                'ACTIVOS_BAJAS': ['TECNOLOGIA', 'MARCA', 'SERIAL', 'MODELO', 'PLACA ', 'OBSERVACIONES DE BAJA'],
                'EQUIPOS_BAJAS_HISTORIAL': ['SERIAL DE EQUIPOS ', 'CARACTERIZTICAS ', 'CIUDAD', 'USUARIO', 'FECHA DE ACTUALIZACIÓN', 'ACTUALIZACIONES', 'MOTIVO DE DAÑO', 'FECHA DE SALIDA'],
                'DEVOLUCIONES_ACTIVOS': ['PLACA ', 'FECHA', 'QUIEN DEVOLVIO', 'ESTADO', 'BACKUP', 'FECHA2'],
                'EQUIPOS_NUEVOS#1': ['SERIAL CPU', 'SERIAL PANTALLAS', 'CIUDAD', 'OBSERVACION '],
                'EQUIPOS_NUEVOS#2': ['NIT', 'Sede', 'Tipo de dispositivo', 'Serial o Mac', 'Modelo', 'IMEI', 'Marca', 'Procesador', 'Tipo de ram', 'Cantidad de ram', 'Tipo de disco', 'Espacio de disco', 'Teclado', 'Mouse', 'Estado', 'Asignado a', 'Area Asignado', 'Cargo Asignado', 'Observaciones', 'Hostname', 'Fecha de creacion', 'Fecha de compra', 'FECHA LLEGADA'],
                'EQUIPOS_NUEVOS#3': ['NIT', 'Sede', 'Tipo de dispositivo', 'Serial o Mac', 'Modelo', 'IMEI', 'Marca', 'Procesador', 'Tipo de ram', 'Cantidad de ram', 'Tipo de disco', 'Espacio de disco', 'Teclado', 'Mouse', 'Estado', 'Asignado a', 'Area Asignado', 'Cargo Asignado', 'Observaciones', 'Hostname', 'Fecha de creacion', 'Fecha de compra', 'FECHA LLEGADA', 'Area o Ciudad'],
                'EQUIPOS_NUEVOS#4': ['MODELO PANTALLAS', 'SERIAL', 'ASIGNADO', 'MODELO CPU', 'SERIAL', 'ASIGNADO'],
                'EQUIPOS_NUEVOS#5': ['Marca', 'Procesador', 'Tipo de ram', 'Cantidad de ram', 'Tipo de disco', 'Espacio de disco', 'Asignado a', 'FECHA LLEGADA', 'Area o Ciudad'],
                'EQUIPOS_NUEVOS#6': ['Tipo de dispositivo', 'Serial o Mac', 'Modelo', 'Marca', 'Procesador', 'Tipo de ram', 'Cantidad de ram', 'Tipo de disco', 'Espacio de disco', 'Asignado a', 'FECHA LLEGADA', 'Area o Ciudad'],
                'EQUIPOS_NUEVOS#7': ['NIT', 'Tipo de dispositivo', 'Serial o Mac', 'Modelo', 'Marca', 'Procesador', 'Tipo de ram', 'Cantidad de ram', 'Tipo de disco', 'Espacio de disco', 'Asignado a', 'FECHA LLEGADA', 'Area o Ciudad'],
                'EQUIPOS_NUEVOS#8': ['NIT', 'Sede', 'Tipo de dispositivo', 'Serial o Mac', 'Modelo', 'Anterior asignado', 'Placa', 'Marca', 'Procesador', 'Tipo de ram', 'Cantidad de ram', 'Tipo de disco', 'Espacio de disco', 'SO', 'Estado', 'Asignado Nuevo', 'Fecha de Asignación', 'Fecha LLegada', 'Area ', 'Marca Monitor', 'Modelo Monitor', 'Serial', 'Placa Monitor', 'PROVEDOOR', 'OC', 'OBSERVACIONES', 'GARANTIA'],
                'EQUIPOS NUEVOS#9': ['NIT', 'SEDE', 'TIPO DE DISPOSITIVO', 'SERIAL O MAC', 'MODELO', 'PLACA', 'MARCA', 'PROCESADOR', 'TIPO DE RAM', 'CANTIDAD DE RAM', 'TIPO DE DISCO', 'ESPACIO DE DISCO', 'SO', 'ESTADO', 'ASIGNADO NUEVO', 'FECHA DE ASIGNACIÓN', 'FECHA LLEGADA', 'AREA ', 'GARANTIA'],
                'CAMBIOSVSMALOS': ['NOMBRE DE LA PARTE', 'CANTIDAD', 'CAMBIOS/OBS'],
                'COMPRA_ARTICULOS': ['NIT', 'ENTIDAD', 'CIUDAD', 'ARTIUCULOS', 'CANTIDAD', 'FECHA'],
                'FALTANTES': ['CIUDAD', 'SERVICIO', 'FUNCIONARIO', 'TIPO_COMPUTADOR ', 'OBSERVACION '],
                'TELEMEDICINA': ['NIT', 'Sede', 'Tipo de dispositivo', 'Serial o Mac', 'Modelo', 'IMEI', 'Marca', 'Procesador', 'Tipo de ram', 'Cantidad de ram', 'Tipo de disco', 'Espacio de disco', 'Estado', 'Asignado a', 'Observaciones', 'FECHA LLEGADA', 'Area'],
                'D2K': ['NIT', 'Sede', 'Tipo de dispositivo', 'Serial o Mac', 'Modelo', 'IMEI', 'Marca', 'Procesador', 'Tipo de ram', 'Cantidad de ram', 'Tipo de disco', 'Espacio de disco', 'Estado', 'Asignado a', 'Observaciones', 'FECHA LLEGADA', 'Area'],
                'THERAPY': ['NIT', 'Sede', 'Tipo de dispositivo', 'Serial o Mac', 'Modelo', 'Marca', 'Procesador', 'Tipo de ram', 'Cantidad de ram', 'Tipo de disco', 'Espacio de disco', 'Estado', 'Asignado a', 'Observaciones', 'FECHA LLEGADA', 'Area'],
                'PHARMA': ['NIT', 'Sede', 'Tipo de dispositivo', 'Serial o Mac', 'Modelo', 'IMEI', 'Marca', 'Procesador', 'Tipo de ram', 'Cantidad de ram', 'Tipo de disco', 'Espacio de disco', 'Teclado', 'Mouse', 'Estado', 'Asignado a', 'Area Asignado', 'Cargo Asignado', 'Observaciones', 'Hostname', 'Fecha de creacion', 'Fecha de compra', 'FECHA LLEGADA', 'Area'],
                'UBA_VIHONCO': ['ENVIADO /CARGADO', 'CIUDAD', 'TECNOLOGIA', 'SERIAL', 'MODELO', 'ANTERIOR ASIGNADO', 'PLACA', 'MARCA', 'PROCESADOR', 'ARQUI RAM', 'CANTIDAD RAM', 'TIPO DE DISCO', 'ESPACIO DISCO', 'SO', 'Estado', 'ASIGNADO NUEVO', 'FECHA', 'FECHA DE LLEGADA', 'AREA', 'MARCA DE  MONITOR', 'MODELO DE MONITOR', 'SERIAL2', 'PLACA DE MONITOR', 'PROVEEDOR ', 'OC', 'OBSERVACIONES', 'DISPONIBLE'],
                'DME-LABORATORIOS': ['ENVIADO /CARGADO', 'CIUDAD', 'TECNOLOGIA', 'SERIAL', 'MODELO', 'NOMBRE', 'PLACA', 'MARCA', 'PROCESADOR', 'ARQUI RAM', 'CANTIDAD RAM', 'TIPO DE DISCO', 'ESPACIO DISCO', 'SO', 'ESTADO', 'ASIGNADO NUEVO', 'FECHA', 'FECHA DE LLEGADA', 'AREA', 'MARCA DE  MONITOR', 'MODELO DE MONITOR', 'SERIAL2', 'PLACA DE MONITOR', 'PROVEEDOR ', 'OC', 'IP', 'MAC', 'OBSERVACIONES', 'DISPONIBLE']
            }
        }

        # Column mapping to database fields
        self.column_mapping = {
            # Common mappings
            'SERIAL': 'serial',
            'MODELO': 'modelo',
            'MARCA': 'marca',
            'PROCESADOR': 'procesador',
            'RAM': 'cantidad_ram',
            'ALMACENAMIENTO': 'espacio_disco',
            'ESTADO': 'estado',
            'DISPOSITIVO': 'tecnologia',
            'SEDE UBICACIÓN': 'ciudad',
            'SEDE': 'ciudad',
            'CIUDAD': 'ciudad',
            'TECNOLOGIA': 'tecnologia',
            'PLACA': 'placa',
            'SO': 'so',
            'ASIGNADO NUEVO': 'asignado_nuevo',
            'ASIGNADO': 'asignado_nuevo',
            'FECHA': 'fecha',
            'FECHA DE LLEGADA': 'fecha_llegada',
            'AREA': 'area',
            'OBSERVACIONES': 'observaciones',
            'PROVEEDOR': 'proveedor',
            'OC': 'oc',
            'DISPONIBLE': 'disponible',
            'NIT': 'nit',
            'TIPO DE DISPOSITIVO': 'tecnologia',
            'SERIAL O MAC': 'serial',
            'TIPO DE RAM': 'arch_ram',
            'CANTIDAD DE RAM': 'cantidad_ram',
            'TIPO DE DISCO': 'tipo_disco',
            'ESPACIO DE DISCO': 'espacio_disco',
            'ASIGNADO A': 'asignado_nuevo',
            'HOSTNAME': 'hostname',
            'IMEI': 'imei',
            'TECLADO': 'teclado',
            'MOUSE': 'mouse',
            'AREA ASIGNADO': 'area',
            'CARGO ASIGNADO': 'cargo_asignado',
            'FECHA DE CREACION': 'fecha_creacion',
            'FECHA DE COMPRA': 'fecha_compra',
            'GARANTIA': 'garantia',
            'IP': 'ip',
            'MAC': 'mac'
        }

    def detect_inventory_type(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect the inventory type and structure from the dataframe"""
        inventory_data = {}

        # Find the main inventory sections
        for idx, row in df.iterrows():
            first_col = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""

            # Check for main sections
            if first_col in self.inventory_types:
                section = first_col
                inventory_data[section] = {}

                # Look for subsections in the following rows
                for sub_idx in range(idx + 1, len(df)):
                    sub_row = df.iloc[sub_idx]
                    sub_first_col = str(sub_row.iloc[0]).strip() if pd.notna(sub_row.iloc[0]) else ""

                    if sub_first_col.endswith(':') or sub_first_col in self.inventory_types[section]:
                        subsection = sub_first_col
                        if subsection in self.inventory_types[section]:
                            # Find header row for this subsection
                            header_row_idx = self._find_header_row(df, sub_idx)
                            if header_row_idx is not None:
                                headers = self._extract_headers(df, header_row_idx)
                                data_rows = self._extract_data_rows(df, header_row_idx + 1, subsection)

                                inventory_data[section][subsection] = {
                                    'headers': headers,
                                    'data': data_rows
                                }
                    elif sub_first_col in self.inventory_types:
                        # New main section
                        break

        return inventory_data

    def _find_header_row(self, df: pd.DataFrame, start_idx: int) -> Optional[int]:
        """Find the header row for a subsection"""
        for idx in range(start_idx + 1, min(start_idx + 10, len(df))):
            row = df.iloc[idx]
            # Check if this row contains header-like values
            non_null_count = row.notna().sum()
            if non_null_count >= 3:  # At least 3 non-null values
                # Check if values look like headers (not numbers, reasonable length)
                header_candidates = []
                for val in row:
                    if pd.notna(val):
                        val_str = str(val).strip()
                        if len(val_str) > 0 and len(val_str) < 50 and not val_str.isdigit():
                            header_candidates.append(val_str)
                if len(header_candidates) >= 3:
                    return idx
        return None

    def _extract_headers(self, df: pd.DataFrame, header_row_idx: int) -> List[str]:
        """Extract headers from a specific row"""
        headers = []
        row = df.iloc[header_row_idx]
        for val in row:
            if pd.notna(val):
                headers.append(str(val).strip())
            else:
                headers.append("")
        return headers

    def _extract_data_rows(self, df: pd.DataFrame, start_idx: int, subsection: str) -> List[Dict[str, Any]]:
        """Extract data rows until next section or end"""
        data_rows = []
        expected_headers = self.inventory_types.get(subsection.split(':')[0], {}).get(subsection, [])

        for idx in range(start_idx, len(df)):
            row = df.iloc[idx]
            first_col = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""

            # Stop if we hit another subsection or main section
            if first_col.endswith(':') or first_col in [k for k in self.inventory_types.keys() if k != subsection.split(':')[0]]:
                break

            # Check if row has actual data (not just headers)
            non_null_count = row.notna().sum()
            if non_null_count >= 2:  # At least 2 non-null values
                row_data = {}
                for col_idx, val in enumerate(row):
                    if col_idx < len(expected_headers) and expected_headers[col_idx]:
                        header = expected_headers[col_idx]
                        if pd.notna(val):
                            row_data[header] = str(val).strip()
                if row_data:
                    data_rows.append(row_data)

        return data_rows

    def map_to_database_format(self, inventory_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Map the parsed data to database format"""
        mapped_data = {
            'equipos_individuales': [],
            'equipos_agrupados': [],
            'accesorios': [],
            'bajas': [],
            'asignaciones': []
        }

        for section, subsections in inventory_data.items():
            for subsection, data in subsections.items():
                headers = data['headers']
                rows = data['data']

                for row in rows:
                    mapped_row = {}
                    for header, value in row.items():
                        db_field = self.column_mapping.get(header.upper(), header.lower().replace(' ', '_'))
                        mapped_row[db_field] = value

                    # Determine target table based on section and content
                    if section == 'INVENTARIO BODEGA MEDELLIN':
                        if subsection == 'OTROS:':
                            mapped_data['accesorios'].append(mapped_row)
                        else:
                            mapped_data['equipos_individuales'].append(mapped_row)
                    elif 'BAJAS' in subsection.upper():
                        mapped_data['bajas'].append(mapped_row)
                    elif 'ASIGNADOS' in subsection.upper() or 'ASIGNADO' in subsection.upper():
                        mapped_data['asignaciones'].append(mapped_row)
                    else:
                        mapped_data['equipos_individuales'].append(mapped_row)

        return mapped_data

    def parse_file(self, file_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """Parse a CSV or XLSX file and return structured data"""
        try:
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, header=None)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path, header=None, encoding='utf-8')
            else:
                raise ValueError("Unsupported file format")

            logging.info(f"Parsing file: {file_path}, shape: {df.shape}")

            # Detect inventory structure
            inventory_data = self.detect_inventory_type(df)

            # Map to database format
            mapped_data = self.map_to_database_format(inventory_data)

            logging.info(f"Parsed data: {sum(len(v) for v in mapped_data.values())} total records")

            return mapped_data

        except Exception as e:
            logging.error(f"Error parsing file {file_path}: {e}")
            raise

    def save_to_json(self, data: Dict[str, List[Dict[str, Any]]], output_path: str):
        """Save parsed data to JSON file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    parser = DisorganizedInventoryParser()

    # Parse the provided files
    files_to_parse = [
        'INVENTARIOS/inventario desorganizados.csv',
        'INVENTARIOS/inventario desorganizados.xlsx'
    ]

    for file_path in files_to_parse:
        if os.path.exists(file_path):
            print(f"Parsing {file_path}...")
            try:
                data = parser.parse_file(file_path)
                json_path = file_path.replace('.csv', '.json').replace('.xlsx', '.json')
                parser.save_to_json(data, json_path)
                print(f"Saved parsed data to {json_path}")
                print(f"Records found: {sum(len(v) for v in data.values())}")
            except Exception as e:
                print(f"Error parsing {file_path}: {e}")
        else:
            print(f"File not found: {file_path}")

if __name__ == "__main__":
    main()
