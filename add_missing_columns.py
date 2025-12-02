import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "workmanager_erp.db")

def add_missing_columns():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Columns to add
    columns_to_add = [
        "codigo_unificado TEXT",
        "anterior_placa TEXT",
        "ip_sede TEXT",
        "mac TEXT",
        "hostname TEXT",
        "ip TEXT",
        "marca_modelo_telemedicina TEXT",
        "mouse TEXT",
        "teclado TEXT",
        "cargo TEXT",
        "contacto TEXT",
        "fecha_asignacion TEXT",
        "cargado_nit TEXT",
        "enviado_nit TEXT",
        "fecha_enviado TEXT",
        "guia TEXT",
        "serial_telemedicina TEXT",
        "tipo_componente_adicional TEXT",
        "marca_modelo_componente_adicional TEXT",
        "serial_componente_adicional TEXT",
        "marca_modelo_telefono TEXT",
        "serial_telefono TEXT",
        "imei_telefono TEXT",
        "marca_modelo_impresora TEXT",
        "ip_impresora TEXT",
        "serial_impresora TEXT",
        "pin_impresora TEXT",
        "marca_modelo_cctv TEXT",
        "serial_cctv TEXT",
        "mueble_asignado TEXT"
    ]

    for column in columns_to_add:
        try:
            c.execute(f"ALTER TABLE equipos_individuales ADD COLUMN {column}")
            print(f"Added column: {column}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {column} already exists")
            else:
                print(f"Error adding {column}: {e}")

    conn.commit()
    conn.close()
    print("Database schema updated successfully.")

if __name__ == "__main__":
    add_missing_columns()
