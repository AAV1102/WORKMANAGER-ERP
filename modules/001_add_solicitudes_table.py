import sqlite3
import os

# Ajusta la ruta si tu base de datos está en otro lugar
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'workmanager_erp.db')

def run_migration():
    """Crea la tabla de solicitudes si no existe."""
    if not os.path.exists(DB_PATH):
        print(f"Error: La base de datos '{DB_PATH}' no fue encontrada.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("Creando la tabla 'solicitudes'...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS solicitudes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empleado_id INTEGER NOT NULL,
                tipo_solicitud TEXT NOT NULL, -- 'vacaciones', 'certificado_laboral', 'liquidacion', etc.
                fecha_inicio DATE,
                fecha_fin DATE,
                descripcion TEXT NOT NULL,
                estado TEXT DEFAULT 'pendiente', -- 'pendiente', 'aprobada', 'rechazada'
                respuesta_admin TEXT, -- Para notas del administrador
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (empleado_id) REFERENCES empleados (id)
            );
        """)
        conn.commit()
        print("Tabla 'solicitudes' creada o ya existente.")
    finally:
        conn.close()

if __name__ == '__main__':
    run_migration()