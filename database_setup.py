import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

from modules.db_utils import (
    get_db_connection,
    load_active_db_path,
    save_active_db_path,
    list_available_dbs,
)
from modules.credentials_config import DEFAULT_ADMIN, DEMO_USER

def init_db():
    conn = sqlite3.connect(load_active_db_path())
    c = conn.cursor()

    # usuarios table (adapted from MySQL schema)
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
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
                )''')

    # sedes table
    c.execute('''CREATE TABLE IF NOT EXISTS sedes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo TEXT NOT NULL UNIQUE,
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
                )''')

    # empleados table
    c.execute('''CREATE TABLE IF NOT EXISTS empleados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cedula TEXT NOT NULL UNIQUE,
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
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )''')

    # equipos_agrupados table (Inventario Tecnológico Agrupado - Un código abarca múltiples equipos)
    c.execute('''CREATE TABLE IF NOT EXISTS equipos_agrupados (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_barras_unificado TEXT UNIQUE,
                    nit TEXT DEFAULT '901.234.567-8',
                    sede_id INTEGER,
                    asignado_anterior TEXT,
                    asignado_actual TEXT,
                    descripcion_general TEXT,
                    estado_general TEXT DEFAULT 'disponible',
                    creador_registro TEXT,
                    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                    trazabilidad_soporte TEXT,
                    documentos_entrega TEXT,
                    observaciones TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sede_id) REFERENCES sedes (id)
                )''')

    # equipos_componentes table (Componentes individuales dentro de un equipo agrupado)
    c.execute('''CREATE TABLE IF NOT EXISTS equipos_componentes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipo_agrupado_id INTEGER,
                    codigo_barras_individual TEXT UNIQUE,
                    tipo_componente TEXT,
                    marca TEXT,
                    modelo TEXT,
                    serial TEXT,
                    caracteristicas TEXT,
                    estado TEXT DEFAULT 'disponible',
                    observaciones TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (equipo_agrupado_id) REFERENCES equipos_agrupados (id)
                )''')

    # accesorios_perifericos table (perifericos y complementos)
    c.execute('''CREATE TABLE IF NOT EXISTS accesorios_perifericos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_parte TEXT,
                    cantidad INTEGER DEFAULT 1,
                    asignado_a TEXT,
                    area TEXT,
                    placa_equipo TEXT,
                    equipo_id INTEGER,
                    fecha_asignacion TEXT,
                    estado TEXT DEFAULT 'disponible',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (equipo_id) REFERENCES equipos_individuales (id)
                )''')


    # hoja_vida_equipos table (movimientos y trazabilidad)
    c.execute('''CREATE TABLE IF NOT EXISTS hoja_vida_equipos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipo_id INTEGER,
                    tipo_equipo TEXT,
                    accion TEXT,
                    usuario_anterior TEXT,
                    usuario_nuevo TEXT,
                    sede_anterior TEXT,
                    sede_nueva TEXT,
                    fecha_accion TEXT,
                    observaciones TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )''')


    # mantenimientos table (historial de mantenimientos)
    c.execute('''CREATE TABLE IF NOT EXISTS mantenimientos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipo_id INTEGER,
                    tipo_equipo TEXT,
                    titulo TEXT,
                    descripcion TEXT,
                    responsable TEXT,
                    fecha_programada TEXT,
                    fecha_ejecucion TEXT,
                    estado TEXT DEFAULT 'pendiente',
                    costo REAL,
                    observaciones TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )''')

    # equipos_individuales table (Inventario Tecnológico Individual - Cada equipo tiene su propio código)
    c.execute('''CREATE TABLE IF NOT EXISTS equipos_individuales (
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
                    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
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
                    FOREIGN KEY (sede_id) REFERENCES sedes (id)
                )''')

    def _table_columns(table_name):
        c.execute(f"PRAGMA table_info({table_name})")
        return {row[1] for row in c.fetchall()}

    def _rename_column(table_name, old_name, new_name):
        columns = _table_columns(table_name)
        if old_name in columns and new_name not in columns:
            c.execute(f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}")

    def _ensure_column(table_name, column_name, column_definition):
        if column_name not in _table_columns(table_name):
            c.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")

    # Ajustar columnas nuevas del inventario individual si faltan
    _rename_column('equipos_individuales', 'enviado_cargado', 'cargado_nit')
    additional_columns = {
        'codigo_unificado': 'TEXT',
        'enviado_nit': 'TEXT',
        'anterior_placa': 'TEXT',
        'ip_sede': 'TEXT',
        'mac': 'TEXT',
        'hostname': 'TEXT',
        'ip': 'TEXT',
        'marca_modelo_telemedicina': 'TEXT',
        'serial_telemedicina': 'TEXT',
        'mouse': 'TEXT',
        'teclado': 'TEXT',
        'cargo': 'TEXT',
        'contacto': 'TEXT',
        'fecha_enviado': 'TEXT',
        'guia': 'TEXT',
        'tipo_componente_adicional': 'TEXT',
        'marca_modelo_componente_adicional': 'TEXT',
        'serial_componente_adicional': 'TEXT',
        'marca_modelo_telefono': 'TEXT',
        'serial_telefono': 'TEXT',
        'imei_telefono': 'TEXT',
        'marca_modelo_impresora': 'TEXT',
        'ip_impresora': 'TEXT',
        'serial_impresora': 'TEXT',
        'pin_impresora': 'TEXT',
        'marca_modelo_cctv': 'TEXT',
        'serial_cctv': 'TEXT',
        'mueble_asignado': 'TEXT'
    }
    for col_name, definition in additional_columns.items():
        _ensure_column('equipos_individuales', col_name, definition)

    # inventario_administrativo table (Muebles)
    c.execute('''CREATE TABLE IF NOT EXISTS inventario_administrativo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_mueble TEXT NOT NULL,
                    nit TEXT DEFAULT '901.234.567-8',
                    sede_id INTEGER,
                    codigo_interno TEXT UNIQUE,
                    estado TEXT DEFAULT 'disponible',
                    descripcion_item TEXT,
                    fecha_compra TEXT,
                    asignado_a TEXT,
                    cantidad INTEGER DEFAULT 1,
                    area_recibe TEXT,
                    cargo_recibe TEXT,
                    observaciones TEXT,
                    creador_registro TEXT,
                    fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                    ultimo_editor TEXT,
                    fecha_edicion TEXT DEFAULT CURRENT_TIMESTAMP,
                    estado_firma TEXT DEFAULT 'pendiente',
                    documentos_soporte TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sede_id) REFERENCES sedes (id)
                )''')

    # inventario_bajas table
    c.execute('''CREATE TABLE IF NOT EXISTS inventario_bajas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    equipo_id INTEGER,
                    tipo_inventario TEXT,
                    motivo_baja TEXT NOT NULL,
                    fecha_baja TEXT DEFAULT CURRENT_TIMESTAMP,
                    responsable_baja TEXT,
                    documentos_soporte TEXT,
                    fotografias_soporte TEXT,
                    observaciones TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (equipo_id) REFERENCES equipos (id)
                )''')

    # tandas_equipos_nuevos table
    c.execute('''CREATE TABLE IF NOT EXISTS tandas_equipos_nuevos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_tanda TEXT UNIQUE,
                    descripcion TEXT,
                    fecha_ingreso TEXT DEFAULT CURRENT_TIMESTAMP,
                    cantidad_equipos INTEGER,
                    proveedor TEXT,
                    valor_total REAL,
                    estado TEXT DEFAULT 'en_proceso',
                    observaciones TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )''')

    # simcards table
    c.execute('''CREATE TABLE IF NOT EXISTS simcards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT NOT NULL UNIQUE,
                    sede_id INTEGER,
                    asignado_a TEXT,
                    estado TEXT DEFAULT 'activa',
                    operador TEXT,
                    plan_datos TEXT,
                    fecha_activacion TEXT,
                    observaciones TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sede_id) REFERENCES sedes (id)
                )''')

    # telefonos_corporativos table
    c.execute('''CREATE TABLE IF NOT EXISTS telefonos_corporativos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    imei TEXT UNIQUE,
                    marca TEXT,
                    modelo TEXT,
                    sede_id INTEGER,
                    asignado_a TEXT,
                    estado TEXT DEFAULT 'disponible',
                    numero_asignado TEXT,
                    fecha_compra TEXT,
                    observaciones TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sede_id) REFERENCES sedes (id)
                )''')

    # facturas table
    c.execute('''CREATE TABLE IF NOT EXISTS facturas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_interno TEXT UNIQUE,
                    numero_factura TEXT NOT NULL,
                    tipo_factura TEXT,
                    valor_factura REAL,
                    nombre_proveedor TEXT,
                    item TEXT,
                    fecha_factura TEXT,
                    autorizado_por TEXT,
                    documentos_soporte TEXT,
                    observaciones TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )''')

    # insumos table
    c.execute('''CREATE TABLE IF NOT EXISTS insumos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_insumo TEXT NOT NULL,
                    serial_equipo TEXT,
                    cantidad_total INTEGER DEFAULT 0,
                    cantidad_disponible INTEGER DEFAULT 0,
                    ubicacion TEXT,
                    asignado_a TEXT,
                    creador_registro TEXT,
                    fecha_asignacion TEXT DEFAULT CURRENT_TIMESTAMP,
                    estado TEXT DEFAULT 'disponible',
                    observaciones TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )''')

    # equipos_biomedicos table
    c.execute('''CREATE TABLE IF NOT EXISTS equipos_biomedicos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_activo TEXT NOT NULL UNIQUE,
                    nombre_equipo TEXT NOT NULL,
                    marca TEXT,
                    modelo TEXT,
                    serial TEXT,
                    clasificacion_riesgo TEXT,
                    registro_invima TEXT,
                    sede_id INTEGER,
                    ubicacion TEXT,
                    estado TEXT DEFAULT 'operativo',
                    fecha_compra TEXT,
                    valor_compra REAL,
                    proveedor TEXT,
                    fecha_ultimo_mantenimiento TEXT,
                    fecha_proximo_mantenimiento TEXT,
                    observaciones TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sede_id) REFERENCES sedes (id)
                )''')

    # licencias_office365 table
    c.execute('''CREATE TABLE IF NOT EXISTS licencias_office365 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    tipo_licencia TEXT,
                    usuario_asignado TEXT,
                    cedula_usuario TEXT,
                    sede_id INTEGER,
                    estado TEXT DEFAULT 'activa',
                    fecha_asignacion TEXT,
                    fecha_vencimiento TEXT,
                    costo_mensual REAL,
                    observaciones TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sede_id) REFERENCES sedes (id)
                )''')

    # licencias table (for the licencias module)
    c.execute('''CREATE TABLE IF NOT EXISTS licencias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software TEXT NOT NULL,
                    license_key TEXT NOT NULL,
                    expiration TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )''')

    # tickets table (Mesa de Ayuda)
    c.execute('''CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_ticket TEXT NOT NULL UNIQUE,
                    titulo TEXT NOT NULL,
                    descripcion TEXT,
                    categoria TEXT,
                    prioridad TEXT DEFAULT 'media',
                    estado TEXT DEFAULT 'abierto',
                    usuario_reporta_id INTEGER,
                    usuario_asignado_id INTEGER,
                    sede_id INTEGER,
                    fecha_apertura TEXT DEFAULT CURRENT_TIMESTAMP,
                    fecha_cierre TEXT,
                    tiempo_respuesta INTEGER,
                    tiempo_resolucion INTEGER,
                    satisfaccion INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (usuario_reporta_id) REFERENCES usuarios (id),
                    FOREIGN KEY (usuario_asignado_id) REFERENCES usuarios (id),
                    FOREIGN KEY (sede_id) REFERENCES sedes (id)
                )''')

    # pacientes table
    c.execute('''CREATE TABLE IF NOT EXISTS pacientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_documento TEXT DEFAULT 'CC',
                    numero_documento TEXT NOT NULL UNIQUE,
                    nombres TEXT NOT NULL,
                    apellidos TEXT NOT NULL,
                    fecha_nacimiento TEXT,
                    genero TEXT,
                    telefono TEXT,
                    email TEXT,
                    direccion TEXT,
                    ciudad TEXT,
                    eps TEXT,
                    tipo_afiliacion TEXT,
                    estado TEXT DEFAULT 'activo',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )''')

    # medicos table
    c.execute('''CREATE TABLE IF NOT EXISTS medicos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cedula TEXT NOT NULL UNIQUE,
                    nombres TEXT NOT NULL,
                    apellidos TEXT NOT NULL,
                    especialidad TEXT,
                    registro_medico TEXT,
                    telefono TEXT,
                    email TEXT,
                    sede_id INTEGER,
                    estado TEXT DEFAULT 'activo',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sede_id) REFERENCES sedes (id)
                )''')

    # citas_medicas table
    c.execute('''CREATE TABLE IF NOT EXISTS citas_medicas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paciente_id INTEGER,
                    medico_id INTEGER,
                    sede_id INTEGER,
                    fecha_cita TEXT NOT NULL,
                    duracion_minutos INTEGER DEFAULT 30,
                    tipo_cita TEXT,
                    especialidad TEXT,
                    estado TEXT DEFAULT 'programada',
                    motivo_consulta TEXT,
                    observaciones TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (paciente_id) REFERENCES pacientes (id),
                    FOREIGN KEY (medico_id) REFERENCES medicos (id),
                    FOREIGN KEY (sede_id) REFERENCES sedes (id)
                )''')

    # asistencias table (Control Biométrico)
    c.execute('''CREATE TABLE IF NOT EXISTS asistencias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empleado_id INTEGER NOT NULL,
                    cedula TEXT,
                    fecha TEXT NOT NULL,
                    hora_entrada TEXT,
                    hora_salida TEXT,
                    sede_id INTEGER,
                    dispositivo_id TEXT,
                    tipo_marcacion TEXT,
                    horas_trabajadas REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (empleado_id) REFERENCES empleados (id),
                    FOREIGN KEY (sede_id) REFERENCES sedes (id)
                )''')

    # hr_requests table (Solicitudes de Recursos Humanos)
    c.execute('''CREATE TABLE IF NOT EXISTS hr_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empleado_id INTEGER NOT NULL,
                    tipo_solicitud TEXT NOT NULL,
                    titulo TEXT NOT NULL,
                    descripcion TEXT,
                    estado TEXT DEFAULT 'pendiente',
                    prioridad TEXT DEFAULT 'media',
                    fecha_solicitud TEXT DEFAULT CURRENT_TIMESTAMP,
                    fecha_aprobacion TEXT,
                    fecha_rechazo TEXT,
                    aprobado_por INTEGER,
                    rechazado_por INTEGER,
                    motivo_rechazo TEXT,
                    observaciones TEXT,
                    documentos_adjuntos TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (empleado_id) REFERENCES empleados (id),
                    FOREIGN KEY (aprobado_por) REFERENCES empleados (id),
                    FOREIGN KEY (rechazado_por) REFERENCES empleados (id)
                )''')

    # hr_approvals table (Historial de aprobaciones)
    c.execute('''CREATE TABLE IF NOT EXISTS hr_approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id INTEGER NOT NULL,
                    aprobado_por INTEGER NOT NULL,
                    decision TEXT NOT NULL,
                    comentarios TEXT,
                    fecha_decision TEXT DEFAULT CURRENT_TIMESTAMP,
                    tiempo_procesamiento INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (request_id) REFERENCES hr_requests (id),
                    FOREIGN KEY (aprobado_por) REFERENCES empleados (id)
                )''')

    # hr_performance_metrics table (Métricas de rendimiento)
    c.execute('''CREATE TABLE IF NOT EXISTS hr_performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empleado_id INTEGER NOT NULL,
                    mes TEXT NOT NULL,
                    anio INTEGER NOT NULL,
                    puntuacion_performance REAL DEFAULT 0,
                    objetivos_cumplidos INTEGER DEFAULT 0,
                    objetivos_total INTEGER DEFAULT 0,
                    horas_trabajadas REAL DEFAULT 0,
                    horas_requeridas REAL DEFAULT 160,
                    evaluador_id INTEGER,
                    comentarios TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (empleado_id) REFERENCES empleados (id),
                    FOREIGN KEY (evaluador_id) REFERENCES empleados (id),
                    UNIQUE(empleado_id, mes, anio)
                )''')

    # hr_reports table (Reportes de RRHH)
    c.execute('''CREATE TABLE IF NOT EXISTS hr_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_reporte TEXT NOT NULL,
                    periodo TEXT NOT NULL,
                    datos JSON,
                    generado_por INTEGER,
                    fecha_generacion TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (generado_por) REFERENCES empleados (id)
                )''')

    # ai_logs table (Logs de IA)
    c.execute('''CREATE TABLE IF NOT EXISTS ai_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    response TEXT,
                    user_id INTEGER,
                    module TEXT,
                    category TEXT DEFAULT 'general',
                    status TEXT DEFAULT 'success',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES usuarios (id)
                )''')

    # RBAC tables
    c.execute('''CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS role_permissions (
                    role_id INTEGER NOT NULL,
                    permission_id INTEGER NOT NULL,
                    PRIMARY KEY (role_id, permission_id),
                    FOREIGN KEY (role_id) REFERENCES roles (id),
                    FOREIGN KEY (permission_id) REFERENCES permissions (id)
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_roles (
                    user_id INTEGER NOT NULL,
                    role_id INTEGER NOT NULL,
                    PRIMARY KEY (user_id, role_id),
                    FOREIGN KEY (user_id) REFERENCES usuarios (id),
                    FOREIGN KEY (role_id) REFERENCES roles (id)
                )''')
    
    conn.commit()
    conn.close()

def seed_db():
    conn = get_db_connection()
    c = conn.cursor()
    try:
        # Seed roles and permissions
        c.execute("INSERT OR IGNORE INTO roles (name, description) VALUES ('admin', 'Administrador del sistema')")
        c.execute("INSERT OR IGNORE INTO roles (name, description) VALUES ('usuario', 'Usuario estándar')")
        c.execute("INSERT OR IGNORE INTO roles (name, description) VALUES ('demo', 'Cuenta demo solo lectura')")
        base_permissions = [
            ('view_admin', 'Ver panel administrativo'),
            ('manage_users', 'Gestionar usuarios y roles'),
            ('view_inventario', 'Ver inventario'),
            ('edit_inventario', 'Editar inventario'),
            ('import_data', 'Importar datos'),
            ('export_data', 'Exportar datos'),
            ('manage_config', 'Gestionar configuración del sistema')
        ]
        for code, name in base_permissions:
            c.execute("INSERT OR IGNORE INTO permissions (code, name) VALUES (?, ?)", (code, name))
        c.execute("SELECT id FROM roles WHERE name='admin'")
        row_admin = c.fetchone()
        if row_admin:
            admin_role_id = row_admin[0]
            c.execute("SELECT id FROM permissions")
            perm_ids = [r[0] for r in c.fetchall()]
            for pid in perm_ids:
                c.execute("INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)", (admin_role_id, pid))

        c.execute("SELECT id FROM roles WHERE name='demo'")
        row_demo = c.fetchone()
        if row_demo:
            demo_role_id = row_demo[0]
            allowed = ['view_admin', 'view_inventario', 'export_data']
            for code in allowed:
                c.execute("SELECT id FROM permissions WHERE code=?", (code,))
                perm_row = c.fetchone()
                if perm_row:
                    c.execute(
                        "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                        (demo_role_id, perm_row[0]),
                    )

        # Insert default sedes
        c.execute('''INSERT OR IGNORE INTO sedes (codigo, nombre, ciudad, departamento, estado) VALUES
                        ('SEDE001', 'Sede Principal Bogotá', 'Bogotá', 'Cundinamarca', 'activa'),
                        ('SEDE002', 'Sede Norte Bogotá', 'Bogotá', 'Cundinamarca', 'activa'),
                        ('SEDE003', 'Sede Sur Bogotá', 'Bogotá', 'Cundinamarca', 'activa'),
                        ('SEDE004', 'Sede Medellín', 'Medellín', 'Antioquia', 'activa'),
                        ('SEDE005', 'Sede Cali', 'Cali', 'Valle del Cauca', 'activa'),
                        ('SEDE006', 'Sede Barranquilla', 'Barranquilla', 'Atlántico', 'activa'),
                        ('SEDE007', 'Sede Cartagena', 'Cartagena', 'Bolívar', 'activa'),
                        ('SEDE008', 'Sede Bucaramanga', 'Bucaramanga', 'Santander', 'activa'),
                        ('SEDE009', 'Sede Pereira', 'Pereira', 'Risaralda', 'activa'),
                        ('SEDE010', 'Sede Manizales', 'Manizales', 'Caldas', 'activa'),
                        ('SEDE011', 'Sede Ibagué', 'Ibagué', 'Tolima', 'activa'),
                        ('SEDE012', 'Sede Villavicencio', 'Villavicencio', 'Meta', 'activa'),
                        ('SEDE013', 'Sede Neiva', 'Neiva', 'Huila', 'activa')''')

        # Indices and additional column adjustments from init_db (these are schema modifications, should ideally be in migrations)
        c.execute("CREATE INDEX IF NOT EXISTS idx_ei_serial ON equipos_individuales(serial)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ei_placa ON equipos_individuales(placa)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_ei_codigo ON equipos_individuales(codigo_barras_individual)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_empleado_cedula ON empleados(cedula)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_empleado_correo ON empleados(correo_office)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_factura_numero ON facturas(numero_factura)")

        def _table_columns(table_name):
            c.execute(f"PRAGMA table_info({table_name})")
            return {row[1] for row in c.fetchall()}

        def _rename_column(table_name, old_name, new_name):
            columns = _table_columns(table_name)
            if old_name in columns and new_name not in columns:
                c.execute(f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}")

        def _ensure_column(table_name, column_name, column_definition):
            if column_name not in _table_columns(table_name):
                c.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")

        # Ajustar columnas nuevas del inventario individual si faltan
        _rename_column('equipos_individuales', 'enviado_cargado', 'cargado_nit')
        additional_columns = {
            'codigo_unificado': 'TEXT',
            'enviado_nit': 'TEXT',
            'anterior_placa': 'TEXT',
            'ip_sede': 'TEXT',
            'mac': 'TEXT',
            'hostname': 'TEXT',
            'ip': 'TEXT',
            'marca_modelo_telemedicina': 'TEXT',
            'serial_telemedicina': 'TEXT',
            'mouse': 'TEXT',
            'teclado': 'TEXT',
            'cargo': 'TEXT',
            'contacto': 'TEXT',
            'fecha_enviado': 'TEXT',
            'guia': 'TEXT',
            'tipo_componente_adicional': 'TEXT',
            'marca_modelo_componente_adicional': 'TEXT',
            'serial_componente_adicional': 'TEXT',
            'marca_modelo_telefono': 'TEXT',
            'serial_telefono': 'TEXT',
            'imei_telefono': 'TEXT',
            'marca_modelo_impresora': 'TEXT',
            'ip_impresora': 'TEXT',
            'serial_impresora': 'TEXT',
            'pin_impresora': 'TEXT',
            'marca_modelo_cctv': 'TEXT',
            'serial_cctv': 'TEXT',
            'mueble_asignado': 'TEXT'
        }
        for col_name, definition in additional_columns.items():
            _ensure_column('equipos_individuales', col_name, definition)

        conn.commit()
    except Exception as e:
        print(f"Error seeding database: {e}")
        conn.rollback()
    finally:
        conn.close()

def ensure_default_admin():
    """
    Crea un usuario administrador por defecto y lo asocia al rol admin si no existe.
    Evita que el login falle por falta de credenciales iniciales.
    """
    conn = get_db_connection()
    c = conn.cursor()
    try:
        def role_id(role_name):
            c.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
            row = c.fetchone()
            return row["id"] if row else None

        admin_hash = generate_password_hash(DEFAULT_ADMIN["password"])
        c.execute("SELECT id FROM usuarios WHERE email = ?", (DEFAULT_ADMIN["email"],))
        existing = c.fetchone()
        if existing:
            admin_id = existing["id"]
            c.execute(
                """
                UPDATE usuarios
                SET cedula=?, nombre=?, apellido=?, nombre_completo=?, password=?, rol='admin', estado='activo'
                WHERE id=?
                """,
                (
                    DEFAULT_ADMIN["cedula"],
                    DEFAULT_ADMIN["nombre"],
                    DEFAULT_ADMIN["apellido"],
                    DEFAULT_ADMIN["nombre_completo"],
                    admin_hash,
                    admin_id,
                ),
            )
        else:
            c.execute(
                """
                INSERT INTO usuarios (cedula, nombre, apellido, nombre_completo, email, password, rol, estado)
                VALUES (?, ?, ?, ?, ?, ?, 'admin', 'activo')
                """,
                (
                    DEFAULT_ADMIN["cedula"],
                    DEFAULT_ADMIN["nombre"],
                    DEFAULT_ADMIN["apellido"],
                    DEFAULT_ADMIN["nombre_completo"],
                    DEFAULT_ADMIN["email"],
                    admin_hash,
                ),
            )
            admin_id = c.lastrowid

        admin_role = role_id("admin") or 1
        c.execute(
            "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)",
            (admin_id, admin_role),
        )

        demo_hash = generate_password_hash(DEMO_USER["password"])
        c.execute("SELECT id FROM usuarios WHERE email = ?", (DEMO_USER["email"],))
        demo_row = c.fetchone()
        if demo_row:
            demo_id = demo_row["id"]
            c.execute(
                """
                UPDATE usuarios
                SET cedula=?, nombre=?, apellido=?, nombre_completo=?, password=?, rol='demo', estado='activo'
                WHERE id=?
                """,
                (
                    DEMO_USER["cedula"],
                    DEMO_USER["nombre"],
                    DEMO_USER["apellido"],
                    DEMO_USER["nombre_completo"],
                    demo_hash,
                    demo_id,
                ),
            )
        else:
            c.execute(
                """
                INSERT INTO usuarios (cedula, nombre, apellido, nombre_completo, email, password, rol, estado)
                VALUES (?, ?, ?, ?, ?, ?, 'demo', 'activo')
                """,
                (
                    DEMO_USER["cedula"],
                    DEMO_USER["nombre"],
                    DEMO_USER["apellido"],
                    DEMO_USER["nombre_completo"],
                    DEMO_USER["email"],
                    demo_hash,
                ),
            )
            demo_id = c.lastrowid

        demo_role = role_id("demo") or role_id("usuario") or 2
        c.execute(
            "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)",
            (demo_id, demo_role),
        )
        conn.commit()
    except Exception as e:
        print(f"Error ensuring default admin/demo users: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    # This block allows you to run database_setup.py directly to initialize and seed the DB
    init_db()
    seed_db()
    ensure_default_admin()
    print("Database initialized, seeded, and default admin/demo users ensured.")
