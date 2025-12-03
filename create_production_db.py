#!/usr/bin/env python3
"""
WORKMANAGER ERP - Script de Inicialización de Base de Datos de Producción

Este script se conecta a una base de datos de producción (PostgreSQL o MySQL/MariaDB)
usando la variable de entorno DATABASE_URL y crea todas las tablas necesarias.

Uso:
1. Asegúrate de tener las librerías necesarias:
   pip install psycopg2-binary mysql-connector-python

2. Configura la variable de entorno con la URL de tu base de datos:
   (En Windows)
   set DATABASE_URL="postgresql://user:password@host:port/dbname"
   (En Linux/macOS)
   export DATABASE_URL="postgresql://user:password@host:port/dbname"

3. Ejecuta el script:
   python create_production_db.py
"""

import os
import sys
import sqlite3
from urllib.parse import urlparse

try:
    import psycopg2
    from psycopg2.extras import DictCursor
except ImportError:
    print("Advertencia: psycopg2 no está instalado. No se podrá conectar a PostgreSQL.")
    psycopg2 = None

try:
    import mysql.connector
except ImportError:
    print("Advertencia: mysql-connector-python no está instalado. No se podrá conectar a MySQL/MariaDB.")
    mysql = None


def get_db_connection():
    """
    Se conecta a la base de datos de producción usando la variable de entorno DATABASE_URL.
    """
    db_url = os.environ.get("DATABASE_URL")

    # Si no hay URL de producción, usamos la base de datos local SQLite.
    if not db_url:
        local_db_path = os.path.join(os.path.dirname(__file__), 'workmanager_erp.db')
        print(f"No se encontró DATABASE_URL. Usando base de datos local SQLite: {local_db_path}")
        return sqlite3.connect(local_db_path), "sqlite"

    scheme = result.scheme.lower()
    conn = None

    print(f"Intentando conectar a la base de datos con el esquema: {scheme}...")

    if 'postgres' in scheme:
        if not psycopg2:
            print("Error: El driver de PostgreSQL (psycopg2) no está instalado.")
            sys.exit(1)
        try:
            conn = psycopg2.connect(
                dbname=result.path[1:],
                user=result.username,
                password=result.password,
                host=result.hostname,
                port=result.port or 5432
            )
            print("Conexión a PostgreSQL exitosa.")
        except Exception as e:
            print(f"Error conectando a PostgreSQL: {e}")
            sys.exit(1)

    elif 'mysql' in scheme or 'mariadb' in scheme:
        if not mysql:
            print("Error: El driver de MySQL (mysql-connector-python) no está instalado.")
            sys.exit(1)
        try:
            conn = mysql.connector.connect(
                host=result.hostname,
                user=result.username,
                password=result.password,
                database=result.path[1:],
                port=result.port or 3306
            )
            print("Conexión a MariaDB/MySQL exitosa.")
        except Exception as e:
            print(f"Error conectando a MariaDB/MySQL: {e}")
            sys.exit(1)
    else:
        print(f"Error: Esquema de base de datos no soportado: {scheme}")
        sys.exit(1)

    return conn, scheme


# --- DEFINICIÓN DE TABLAS ---
# Adaptadas para PostgreSQL (SERIAL) y MySQL/MariaDB (AUTO_INCREMENT)

TABLE_DEFINITIONS = {
    "sqlite": {
        # Las definiciones para SQLite son muy similares a PostgreSQL, pero usamos INTEGER PRIMARY KEY AUTOINCREMENT
        # y los tipos de datos son más genéricos (TEXT, INTEGER, REAL).
        "usuarios": """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cedula TEXT,
                nombre TEXT NOT NULL,
                apellido TEXT,
                nombre_completo TEXT,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                rol TEXT DEFAULT 'usuario',
                cargo TEXT,
                departamento TEXT,
                telefono TEXT,
                documento TEXT,
                tipo_documento TEXT DEFAULT 'CC',
                fecha_ingreso TEXT,
                fecha_retiro TEXT,
                estado TEXT DEFAULT 'activo',
                estado_usuario TEXT DEFAULT 'Activo',
                activo INTEGER DEFAULT 1,
                empresa_id INTEGER,
                sede_id INTEGER,
                razon_social TEXT,
                ciudad TEXT,
                codigo_biometrico TEXT,
                usuario_windows TEXT,
                contrasena_windows TEXT,
                correo_office TEXT,
                usuario_quiron TEXT,
                contrasena_quiron TEXT,
                observaciones TEXT,
                requiere_cambio_password INTEGER DEFAULT 0,
                ultimo_acceso TEXT,
                intentos_fallidos INTEGER DEFAULT 0,
                bloqueado_hasta TEXT,
                token_recuperacion TEXT,
                token_expiracion TEXT,
                two_factor_secret TEXT,
                two_factor_enabled INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
        "sedes": """
            CREATE TABLE IF NOT EXISTS sedes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                nombre TEXT NOT NULL,
                direccion TEXT,
                ciudad TEXT,
                departamento TEXT,
                telefono TEXT,
                email TEXT,
                responsable TEXT,
                estado TEXT DEFAULT 'activa',
                ip_biometrico TEXT,
                puerto_biometrico INTEGER DEFAULT 4370,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
        "empleados": """
            CREATE TABLE IF NOT EXISTS empleados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cedula TEXT UNIQUE,
                nombre TEXT NOT NULL,
                apellido TEXT,
                cargo TEXT,
                departamento TEXT,
                fecha_ingreso TEXT,
                razon_social TEXT,
                ciudad TEXT,
                codigo_unico_hv_equipo TEXT,
                usuario_windows TEXT,
                contrasena_windows TEXT,
                correo_office TEXT,
                usuario_quiron TEXT,
                contrasena_quiron TEXT,
                observaciones TEXT,
                codigo_biometrico TEXT,
                estado TEXT DEFAULT 'activo',
                telefono TEXT,
                email TEXT,
                salario REAL,
                performance INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                fecha_nacimiento TEXT,
                fecha_expedicion TEXT,
                lugar_nacimiento TEXT,
                lugar_expedicion TEXT,
                mes_cumpleanos TEXT,
                tipo_sangre TEXT,
                estado_civil TEXT,
                numero_hijos TEXT,
                genero TEXT,
                empresa TEXT,
                dependencia TEXT,
                nivel_educativo TEXT,
                tarifa TEXT,
                tiempo TEXT,
                afp TEXT,
                eps TEXT,
                cesantias TEXT,
                contrataciones_anteriores TEXT,
                fecha_ultimo_contrato TEXT,
                fecha_proximo_vencimiento TEXT,
                plazo TEXT,
                dias_vencimiento TEXT,
                camisa TEXT,
                pantalon TEXT,
                zapatos TEXT,
                bata TEXT,
                ccf TEXT,
                riesgo TEXT,
                numeral_otro_si TEXT
            )""",
        "equipos_individuales": """
            CREATE TABLE IF NOT EXISTS equipos_individuales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_barras_individual TEXT UNIQUE,
                codigo_unificado TEXT,
                entrada_oc_compra TEXT,
                cargado_nit TEXT,
                enviado_nit TEXT,
                ciudad TEXT,
                tecnologia TEXT,
                serial TEXT,
                modelo TEXT,
                anterior_asignado TEXT,
                anterior_placa TEXT,
                placa TEXT,
                marca TEXT,
                procesador TEXT,
                arch_ram TEXT,
                cantidad_ram TEXT,
                tipo_disco TEXT,
                espacio_disco TEXT,
                so TEXT,
                estado TEXT DEFAULT 'disponible',
                asignado_nuevo TEXT,
                fecha TEXT,
                fecha_llegada TEXT,
                area TEXT,
                marca_monitor TEXT,
                modelo_monitor TEXT,
                serial_monitor TEXT,
                placa_monitor TEXT,
                proveedor TEXT,
                oc TEXT,
                observaciones TEXT,
                disponible TEXT DEFAULT 'Si',
                sede_id INTEGER,
                ip_sede TEXT,
                creador_registro TEXT,
                fecha_creacion TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                mac TEXT,
                hostname TEXT,
                ip TEXT,
                marca_modelo_telemedicina TEXT,
                serial_telemedicina TEXT,
                mouse TEXT,
                teclado TEXT,
                cargo TEXT,
                contacto TEXT,
                fecha_enviado TEXT,
                guia TEXT,
                tipo_componente_adicional TEXT,
                marca_modelo_componente_adicional TEXT,
                serial_componente_adicional TEXT,
                marca_modelo_telefono TEXT,
                serial_telefono TEXT,
                imei_telefono TEXT,
                marca_modelo_impresora TEXT,
                ip_impresora TEXT,
                serial_impresora TEXT,
                pin_impresora TEXT,
                marca_modelo_cctv TEXT,
                serial_cctv TEXT,
                mueble_asignado TEXT,
                origen_dato TEXT DEFAULT 'manual'
            )""",
        "equipos_agrupados": """
            CREATE TABLE IF NOT EXISTS equipos_agrupados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_barras_unificado TEXT UNIQUE,
                nit TEXT DEFAULT '901.234.567-8',
                sede_id INTEGER,
                asignado_anterior TEXT,
                asignado_actual TEXT,
                descripcion_general TEXT,
                estado_general TEXT DEFAULT 'disponible',
                creador_registro TEXT,
                fecha_creacion TEXT,
                trazabilidad_soporte TEXT,
                documentos_entrega TEXT,
                observaciones TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
        "notificaciones": """
            CREATE TABLE IF NOT EXISTS notificaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                url TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""",
    },
    "postgres": {
        "usuarios": """
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                cedula TEXT,
                nombre TEXT NOT NULL,
                apellido TEXT,
                nombre_completo TEXT,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                rol TEXT DEFAULT 'usuario',
                cargo TEXT,
                departamento TEXT,
                telefono TEXT,
                documento TEXT,
                tipo_documento TEXT DEFAULT 'CC',
                fecha_ingreso TEXT,
                fecha_retiro TEXT,
                estado TEXT DEFAULT 'activo',
                estado_usuario TEXT DEFAULT 'Activo',
                activo INTEGER DEFAULT 1,
                empresa_id INTEGER,
                sede_id INTEGER,
                razon_social TEXT,
                ciudad TEXT,
                codigo_biometrico TEXT,
                usuario_windows TEXT,
                contrasena_windows TEXT,
                correo_office TEXT,
                usuario_quiron TEXT,
                contrasena_quiron TEXT,
                observaciones TEXT,
                requiere_cambio_password INTEGER DEFAULT 0,
                ultimo_acceso TIMESTAMP WITH TIME ZONE,
                intentos_fallidos INTEGER DEFAULT 0,
                bloqueado_hasta TIMESTAMP WITH TIME ZONE,
                token_recuperacion TEXT,
                token_expiracion TIMESTAMP WITH TIME ZONE,
                two_factor_secret TEXT,
                two_factor_enabled INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
        "sedes": """
            CREATE TABLE IF NOT EXISTS sedes (
                id SERIAL PRIMARY KEY,
                codigo TEXT UNIQUE,
                nombre TEXT NOT NULL,
                direccion TEXT,
                ciudad TEXT,
                departamento TEXT,
                telefono TEXT,
                email TEXT,
                responsable TEXT,
                estado TEXT DEFAULT 'activa',
                ip_biometrico TEXT,
                puerto_biometrico INTEGER DEFAULT 4370,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
        "empleados": """
            CREATE TABLE IF NOT EXISTS empleados (
                id SERIAL PRIMARY KEY,
                cedula TEXT UNIQUE,
                nombre TEXT NOT NULL,
                apellido TEXT,
                cargo TEXT,
                departamento TEXT,
                fecha_ingreso TEXT,
                razon_social TEXT,
                ciudad TEXT,
                codigo_unico_hv_equipo TEXT,
                usuario_windows TEXT,
                contrasena_windows TEXT,
                correo_office TEXT,
                usuario_quiron TEXT,
                contrasena_quiron TEXT,
                observaciones TEXT,
                codigo_biometrico TEXT,
                estado TEXT DEFAULT 'activo',
                telefono TEXT,
                email TEXT,
                salario REAL,
                performance INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                fecha_nacimiento TEXT,
                fecha_expedicion TEXT,
                lugar_nacimiento TEXT,
                lugar_expedicion TEXT,
                mes_cumpleanos TEXT,
                tipo_sangre TEXT,
                estado_civil TEXT,
                numero_hijos TEXT,
                genero TEXT,
                empresa TEXT,
                dependencia TEXT,
                nivel_educativo TEXT,
                tarifa TEXT,
                tiempo TEXT,
                afp TEXT,
                eps TEXT,
                cesantias TEXT,
                contrataciones_anteriores TEXT,
                fecha_ultimo_contrato TEXT,
                fecha_proximo_vencimiento TEXT,
                plazo TEXT,
                dias_vencimiento TEXT,
                camisa TEXT,
                pantalon TEXT,
                zapatos TEXT,
                bata TEXT,
                ccf TEXT,
                riesgo TEXT,
                numeral_otro_si TEXT
            )""",
        "equipos_individuales": """
            CREATE TABLE IF NOT EXISTS equipos_individuales (
                id SERIAL PRIMARY KEY,
                codigo_barras_individual TEXT UNIQUE,
                codigo_unificado TEXT,
                entrada_oc_compra TEXT,
                cargado_nit TEXT,
                enviado_nit TEXT,
                ciudad TEXT,
                tecnologia TEXT,
                serial TEXT,
                modelo TEXT,
                anterior_asignado TEXT,
                anterior_placa TEXT,
                placa TEXT,
                marca TEXT,
                procesador TEXT,
                arch_ram TEXT,
                cantidad_ram TEXT,
                tipo_disco TEXT,
                espacio_disco TEXT,
                so TEXT,
                estado TEXT DEFAULT 'disponible',
                asignado_nuevo TEXT,
                fecha TEXT,
                fecha_llegada TEXT,
                area TEXT,
                marca_monitor TEXT,
                modelo_monitor TEXT,
                serial_monitor TEXT,
                placa_monitor TEXT,
                proveedor TEXT,
                oc TEXT,
                observaciones TEXT,
                disponible TEXT DEFAULT 'Si',
                sede_id INTEGER,
                ip_sede TEXT,
                creador_registro TEXT,
                fecha_creacion TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                mac TEXT,
                hostname TEXT,
                ip TEXT,
                marca_modelo_telemedicina TEXT,
                serial_telemedicina TEXT,
                mouse TEXT,
                teclado TEXT,
                cargo TEXT,
                contacto TEXT,
                fecha_enviado TEXT,
                guia TEXT,
                tipo_componente_adicional TEXT,
                marca_modelo_componente_adicional TEXT,
                serial_componente_adicional TEXT,
                marca_modelo_telefono TEXT,
                serial_telefono TEXT,
                imei_telefono TEXT,
                marca_modelo_impresora TEXT,
                ip_impresora TEXT,
                serial_impresora TEXT,
                pin_impresora TEXT,
                marca_modelo_cctv TEXT,
                serial_cctv TEXT,
                mueble_asignado TEXT,
                origen_dato TEXT DEFAULT 'manual'
            )""",
        "equipos_agrupados": """
            CREATE TABLE IF NOT EXISTS equipos_agrupados (
                id SERIAL PRIMARY KEY,
                codigo_barras_unificado TEXT UNIQUE,
                nit TEXT DEFAULT '901.234.567-8',
                sede_id INTEGER,
                asignado_anterior TEXT,
                asignado_actual TEXT,
                descripcion_general TEXT,
                estado_general TEXT DEFAULT 'disponible',
                creador_registro TEXT,
                fecha_creacion TEXT,
                trazabilidad_soporte TEXT,
                documentos_entrega TEXT,
                observaciones TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
        "notificaciones": """
            CREATE TABLE IF NOT EXISTS notificaciones (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                url TEXT,
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )""",
        # Añadir el resto de las tablas aquí...
    },
    "mysql": {
        "usuarios": """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cedula VARCHAR(255),
                nombre VARCHAR(255) NOT NULL,
                apellido VARCHAR(255),
                nombre_completo VARCHAR(255),
                email VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                rol VARCHAR(50) DEFAULT 'usuario',
                cargo VARCHAR(255),
                departamento VARCHAR(255),
                telefono VARCHAR(50),
                documento VARCHAR(255),
                tipo_documento VARCHAR(50) DEFAULT 'CC',
                fecha_ingreso DATE,
                fecha_retiro DATE,
                estado VARCHAR(50) DEFAULT 'activo',
                estado_usuario VARCHAR(50) DEFAULT 'Activo',
                activo BOOLEAN DEFAULT TRUE,
                empresa_id INTEGER,
                sede_id INTEGER,
                razon_social VARCHAR(255),
                ciudad VARCHAR(255),
                codigo_biometrico VARCHAR(255),
                usuario_windows VARCHAR(255),
                contrasena_windows VARCHAR(255),
                correo_office VARCHAR(255),
                usuario_quiron VARCHAR(255),
                contrasena_quiron VARCHAR(255),
                observaciones TEXT,
                requiere_cambio_password BOOLEAN DEFAULT FALSE,
                ultimo_acceso DATETIME,
                intentos_fallidos INTEGER DEFAULT 0,
                bloqueado_hasta DATETIME,
                token_recuperacion VARCHAR(255),
                token_expiracion DATETIME,
                two_factor_secret VARCHAR(255),
                two_factor_enabled BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;""",
        "sedes": """
            CREATE TABLE IF NOT EXISTS sedes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                codigo VARCHAR(50) UNIQUE,
                nombre VARCHAR(255) NOT NULL,
                direccion TEXT,
                ciudad VARCHAR(255),
                departamento VARCHAR(255),
                telefono VARCHAR(50),
                email VARCHAR(255),
                responsable VARCHAR(255),
                estado VARCHAR(50) DEFAULT 'activa',
                ip_biometrico VARCHAR(50),
                puerto_biometrico INTEGER DEFAULT 4370,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;""",
        "empleados": """
            CREATE TABLE IF NOT EXISTS empleados (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cedula VARCHAR(255) UNIQUE,
                nombre VARCHAR(255) NOT NULL,
                apellido VARCHAR(255),
                cargo VARCHAR(255),
                departamento VARCHAR(255),
                fecha_ingreso DATE,
                razon_social VARCHAR(255),
                ciudad VARCHAR(255),
                codigo_unico_hv_equipo VARCHAR(255),
                usuario_windows VARCHAR(255),
                contrasena_windows VARCHAR(255),
                correo_office VARCHAR(255),
                usuario_quiron VARCHAR(255),
                contrasena_quiron VARCHAR(255),
                observaciones TEXT,
                codigo_biometrico VARCHAR(255),
                estado VARCHAR(50) DEFAULT 'activo',
                telefono VARCHAR(50),
                email VARCHAR(255),
                salario DECIMAL(15,2),
                performance INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                fecha_nacimiento DATE,
                fecha_expedicion DATE,
                lugar_nacimiento VARCHAR(255),
                lugar_expedicion VARCHAR(255),
                mes_cumpleanos VARCHAR(20),
                tipo_sangre VARCHAR(10),
                estado_civil VARCHAR(50),
                numero_hijos VARCHAR(10),
                genero VARCHAR(50),
                empresa VARCHAR(255),
                dependencia VARCHAR(255),
                nivel_educativo VARCHAR(255),
                tarifa VARCHAR(50),
                tiempo VARCHAR(50),
                afp VARCHAR(255),
                eps VARCHAR(255),
                cesantias VARCHAR(255),
                contrataciones_anteriores TEXT,
                fecha_ultimo_contrato DATE,
                fecha_proximo_vencimiento DATE,
                plazo VARCHAR(50),
                dias_vencimiento VARCHAR(50),
                camisa VARCHAR(50),
                pantalon VARCHAR(50),
                zapatos VARCHAR(50),
                bata VARCHAR(50),
                ccf VARCHAR(255),
                riesgo VARCHAR(50),
                numeral_otro_si TEXT
            ) ENGINE=InnoDB;""",
        "equipos_individuales": """
            CREATE TABLE IF NOT EXISTS equipos_individuales (
                id INT AUTO_INCREMENT PRIMARY KEY,
                codigo_barras_individual VARCHAR(255) UNIQUE,
                codigo_unificado VARCHAR(255),
                entrada_oc_compra VARCHAR(255),
                cargado_nit VARCHAR(255),
                enviado_nit VARCHAR(255),
                ciudad VARCHAR(255),
                tecnologia VARCHAR(255),
                serial VARCHAR(255),
                modelo VARCHAR(255),
                anterior_asignado VARCHAR(255),
                anterior_placa VARCHAR(255),
                placa VARCHAR(255),
                marca VARCHAR(255),
                procesador VARCHAR(255),
                arch_ram VARCHAR(255),
                cantidad_ram VARCHAR(255),
                tipo_disco VARCHAR(255),
                espacio_disco VARCHAR(255),
                so VARCHAR(255),
                estado VARCHAR(50) DEFAULT 'disponible',
                asignado_nuevo VARCHAR(255),
                fecha VARCHAR(50),
                fecha_llegada VARCHAR(50),
                area VARCHAR(255),
                marca_monitor VARCHAR(255),
                modelo_monitor VARCHAR(255),
                serial_monitor VARCHAR(255),
                placa_monitor VARCHAR(255),
                proveedor VARCHAR(255),
                oc VARCHAR(255),
                observaciones TEXT,
                disponible VARCHAR(10) DEFAULT 'Si',
                sede_id INTEGER,
                ip_sede VARCHAR(50),
                creador_registro VARCHAR(255),
                fecha_creacion VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                mac VARCHAR(50),
                hostname VARCHAR(255),
                ip VARCHAR(50),
                marca_modelo_telemedicina VARCHAR(255),
                serial_telemedicina VARCHAR(255),
                mouse VARCHAR(255),
                teclado VARCHAR(255),
                cargo VARCHAR(255),
                contacto VARCHAR(255),
                fecha_enviado VARCHAR(50),
                guia VARCHAR(255),
                tipo_componente_adicional VARCHAR(255),
                marca_modelo_componente_adicional VARCHAR(255),
                serial_componente_adicional VARCHAR(255),
                marca_modelo_telefono VARCHAR(255),
                serial_telefono VARCHAR(255),
                imei_telefono VARCHAR(255),
                marca_modelo_impresora VARCHAR(255),
                ip_impresora VARCHAR(50),
                serial_impresora VARCHAR(255),
                pin_impresora VARCHAR(50),
                marca_modelo_cctv VARCHAR(255),
                serial_cctv VARCHAR(255),
                mueble_asignado VARCHAR(255),
                origen_dato VARCHAR(50) DEFAULT 'manual'
            ) ENGINE=InnoDB;""",
        "equipos_agrupados": """
            CREATE TABLE IF NOT EXISTS equipos_agrupados (
                id INT AUTO_INCREMENT PRIMARY KEY,
                codigo_barras_unificado VARCHAR(255) UNIQUE,
                nit VARCHAR(50) DEFAULT '901.234.567-8',
                sede_id INTEGER,
                asignado_anterior VARCHAR(255),
                asignado_actual VARCHAR(255),
                descripcion_general TEXT,
                estado_general VARCHAR(50) DEFAULT 'disponible',
                creador_registro VARCHAR(255),
                fecha_creacion VARCHAR(50),
                trazabilidad_soporte TEXT,
                documentos_entrega TEXT,
                observaciones TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;""",
        "notificaciones": """
            CREATE TABLE IF NOT EXISTS notificaciones (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                url TEXT,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB;""",
        # Añadir el resto de las tablas aquí...
    }
}


def create_tables(conn, db_type):
    """
    Ejecuta las sentencias CREATE TABLE para el tipo de base de datos especificado.
    """
    if db_type not in TABLE_DEFINITIONS:
        print(f"Error: No hay definiciones de tablas para el tipo de base de datos '{db_type}'")
        return

    if db_type == 'sqlite':
        cursor = conn.cursor()
    elif db_type == 'mysql':
        cursor = conn.cursor()
    else: # Para PostgreSQL
        cursor = conn.cursor()

    definitions = TABLE_DEFINITIONS[db_type]
    total_tables = len(definitions)
    created_count = 0

    print(f"\nIniciando creación de {total_tables} tablas para {db_type.upper()}...")

    for table_name, create_sql in definitions.items():
        try:
            print(f"  - Creando tabla '{table_name}'...", end="")
            cursor.execute(create_sql)
            print(" OK")
            created_count += 1
        except Exception as e:
            print(f" FALLÓ. Error: {e}")
            # En PostgreSQL, una transacción fallida debe ser revertida
            if db_type == 'postgres':
                conn.rollback()
            # Para MySQL, el motor InnoDB podría haber hecho rollback automático de la sentencia

    # Solo hacer commit si no es MySQL (que puede tener autocommit)
    if db_type in ['postgres', 'sqlite']:
        conn.commit()

    cursor.close()

    print(f"\nProceso finalizado. {created_count}/{total_tables} tablas creadas o verificadas.")


if __name__ == "__main__":
    print("======================================================================")
    print("== WORKMANAGER ERP - INICIALIZADOR DE BASE DE DATOS DE PRODUCCIÓN ==")
    print("======================================================================")

    connection, db_type = get_db_connection()

    if connection:
        # Determinar el tipo de base de datos para usar las sentencias SQL correctas.
        if db_type == 'sqlite':
            create_tables(connection, 'sqlite')
        if 'postgres' in db_type:
            create_tables(connection, 'postgres')
        elif 'mysql' in db_type or 'mariadb' in db_type:
            create_tables(connection, 'mysql')

        connection.close()
        print("\n¡Base de datos lista para usar!")
    else:
        print("\nNo se pudo establecer conexión con la base de datos. Revisa la variable DATABASE_URL.")