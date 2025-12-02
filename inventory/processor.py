# flask-todo-app/inventory/processor.py

import pandas as pd
import os
import glob
from datetime import datetime, timezone

def process_inventory_files(upload_folder):
    """Procesa los archivos de inventario, los limpia y devuelve un DataFrame listo para la DB."""
    try:
        all_xlsx_files = glob.glob(os.path.join(upload_folder, '*.xlsx'))
        archivos_inventario_filtrados = []
        nombre_archivo_sedes = "Sedes.xlsx"
        path_sedes = os.path.join(upload_folder, nombre_archivo_sedes)

        if not os.path.exists(path_sedes):
            return None, "Error: El archivo 'Sedes.xlsx' no fue subido."

        for f in all_xlsx_files:
            if os.path.basename(f).lower() == nombre_archivo_sedes.lower(): continue
            archivos_inventario_filtrados.append(f)

        if not archivos_inventario_filtrados:
            return None, "Error: No se subieron archivos de inventario (además de Sedes.xlsx)."

        lista_de_dataframes = []
        columna_serial = 'Serial o Mac'
        for archivo in archivos_inventario_filtrados:
            df_parcial = pd.read_excel(archivo, header=1)
            if columna_serial not in df_parcial.columns: continue
            df_parcial.dropna(subset=[columna_serial], inplace=True)
            df_parcial['archivo_origen'] = os.path.basename(archivo)
            lista_de_dataframes.append(df_parcial)

        if not lista_de_dataframes:
            return None, "Error: Ningún archivo de inventario contenía datos válidos."
        
        df_informe = pd.concat(lista_de_dataframes, ignore_index=True)
        df_sedes = pd.read_excel(path_sedes, sheet_name='Sedes')

        if columna_serial in df_informe.columns:
            df_informe['__non_null_count__'] = df_informe.count(axis=1)
            df_informe.sort_values(by=[columna_serial, '__non_null_count__'], ascending=[True, False], inplace=True)
            df_informe.drop_duplicates(subset=[columna_serial], keep='first', inplace=True)
            df_informe.drop(columns=['__non_null_count__'], inplace=True)

        mapa_estandarizacion = {
            'Marca': {'hewlett-packard':'HP', 'lenovo':'Lenovo', 'dell':'Dell'},
            'Tipo de dispositivo': {'laptop':'Portátil', 'portatil':'Portátil', 'computador':'PC', 'todo en uno':'AIO'}
        }
        for columna, mapeo in mapa_estandarizacion.items():
            if columna in df_informe.columns:
                df_informe[columna] = df_informe[columna].astype(str).str.lower().map(mapeo).fillna(df_informe[columna])

        sede_ip_map = df_sedes.set_index('Sede')['IP_Sede'].to_dict() if 'Sede' in df_sedes.columns and 'IP_Sede' in df_sedes.columns else {}
        df_informe['ip_sede'] = df_informe['Sede'].map(sede_ip_map).fillna('')
        df_informe['disponible'] = df_informe['Asignado a'].apply(lambda x: "NO" if pd.notna(x) and str(x).strip() else "SI")
        df_informe['fecha_ultima_modificacion'] = datetime.now(timezone.utc)

        # Renombrar columnas para que coincidan con el modelo de la base de datos
        df_informe.rename(columns=lambda c: c.replace(' ', '_').lower(), inplace=True)
        if 'serial_o_mac' in df_informe.columns:
            df_informe.rename(columns={'serial_o_mac': 'serial'}, inplace=True)
        
        return df_informe, None

    except Exception as e:
        return None, f"Error inesperado durante el procesamiento: {e}"
