-- WorkManager ERP - Base de Datos Completa
-- Versión: 3.0
-- Creado por Anderson Ayala Vera (AAV) - Todos los derechos reservados © 2025
-- Compatible con MySQL 8.0+, PostgreSQL 12+, SQLite 3.30+

-- =========================================
-- CONFIGURACIÓN INICIAL
-- =========================================

-- Configurar charset y collation para MySQL
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- =========================================
-- TABLAS DE CONFIGURACIÓN DEL SISTEMA
-- =========================================

CREATE TABLE IF NOT EXISTS config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    `key` VARCHAR(100) NOT NULL UNIQUE,
    value TEXT,
    description VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insertar configuraciones por defecto (solo si no existen)
INSERT IGNORE INTO config (`key`, value, description) VALUES
('system_version', '3.0', 'Versión del sistema WorkManager ERP'),
('company_name', 'Integral IPS', 'Nombre de la empresa'),
('system_name', 'WorkManager ERP', 'Nombre del sistema'),
('developer', 'Anderson Ayala Vera (AAV)', 'Desarrollador principal'),
('db_version', '1.0', 'Versión de la base de datos'),
('ad_sync_enabled', '0', 'Sincronización Active Directory habilitada'),
('ad_last_sync', NULL, 'Última sincronización AD'),
('smtp_host', 'smtp.gmail.com', 'Servidor SMTP'),
('smtp_port', '587', 'Puerto SMTP'),
('two_factor_required', '0', '2FA requerido para admins'),
('session_timeout', '3600', 'Tiempo de expiración de sesión'),
('max_login_attempts', '5', 'Máximo intentos de login'),
('lockout_time', '900', 'Tiempo de bloqueo por intentos fallidos'),
('backup_retention_days', '30', 'Días de retención de backups'),
('log_retention_days', '90', 'Días de retención de logs');

-- =========================================
-- TABLAS DE USUARIOS Y AUTENTICACIÓN
-- =========================================

CREATE TABLE IF NOT EXISTS usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombreUsuario VARCHAR(50) NOT NULL UNIQUE,
    contrasena VARCHAR(255) NOT NULL,
    nombre VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    rol ENUM('super_admin', 'admin_sistemas', 'admin_rrhh', 'user', 'guest') DEFAULT 'user',
    estado ENUM('activo', 'inactivo', 'suspendido') DEFAULT 'activo',
    intentos_fallidos INT DEFAULT 0,
    ultimo_intento_fallido DATETIME NULL,
    ultimo_login DATETIME NULL,
    remember_token VARCHAR(255) NULL,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(255) NULL,
    backup_codes TEXT NULL, -- JSON array de códigos hasheados
    ad_sync BOOLEAN DEFAULT FALSE,
    ad_last_sync DATETIME NULL,
    departamento VARCHAR(100),
    cargo VARCHAR(100),
    telefono VARCHAR(20),
    celular VARCHAR(20),
    jefe VARCHAR(100),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla de permisos
CREATE TABLE IF NOT EXISTS permisos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    idUsuario INT NOT NULL,
    permiso VARCHAR(100) NOT NULL,
    FOREIGN KEY (idUsuario) REFERENCES usuarios(id) ON DELETE CASCADE,
    UNIQUE KEY unique_permiso (idUsuario, permiso)
);

-- Insertar usuario administrador por defecto (solo si no existe)
INSERT IGNORE INTO usuarios (id, nombreUsuario, contrasena, nombre, email, rol, estado) VALUES
(1, 'admin', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Administrador', 'admin@workmanager.com', 'super_admin', 'activo');

-- Permisos del administrador
INSERT INTO permisos (idUsuario, permiso) VALUES
(1, 'ver_dashboard'),
(1, 'ver_usuarios'),
(1, 'crear_usuarios'),
(1, 'editar_usuarios'),
(1, 'eliminar_usuarios'),
(1, 'ver_inventario'),
(1, 'crear_inventario'),
(1, 'editar_inventario'),
(1, 'eliminar_inventario'),
(1, 'ver_tickets'),
(1, 'crear_tickets'),
(1, 'editar_tickets'),
(1, 'cerrar_tickets'),
(1, 'ver_rrhh'),
(1, 'crear_rrhh'),
(1, 'editar_rrhh'),
(1, 'ver_reportes'),
(1, 'exportar_reportes'),
(1, 'config_sistema'),
(1, 'backup_database'),
(1, 'ver_logs');

-- =========================================
-- TABLAS DE EMPLEADOS (RRHH)
-- =========================================

CREATE TABLE IF NOT EXISTS empleados (
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT NULL,
    numero_identificacion VARCHAR(20) UNIQUE NOT NULL,
    tipo_identificacion ENUM('CC', 'CE', 'TI', 'PAS') DEFAULT 'CC',
    primer_nombre VARCHAR(50) NOT NULL,
    segundo_nombre VARCHAR(50),
    primer_apellido VARCHAR(50) NOT NULL,
    segundo_apellido VARCHAR(50),
    fecha_nacimiento DATE,
    genero ENUM('M', 'F', 'Otro') DEFAULT 'M',
    estado_civil ENUM('Soltero', 'Casado', 'Divorciado', 'Viudo', 'Union Libre') DEFAULT 'Soltero',
    email_personal VARCHAR(100),
    telefono_personal VARCHAR(20),
    celular_personal VARCHAR(20),
    direccion VARCHAR(255),
    ciudad VARCHAR(100),
    departamento VARCHAR(100),
    pais VARCHAR(100) DEFAULT 'Colombia',

    -- Información laboral
    fecha_ingreso DATE NOT NULL,
    fecha_retiro DATE NULL,
    tipo_contrato ENUM('Indefinido', 'Fijo', 'Obra Labor', 'Aprendizaje', 'Prestación Servicios') DEFAULT 'Indefinido',
    cargo VARCHAR(100),
    departamento_laboral VARCHAR(100),
    salario_base DECIMAL(15,2),
    auxilio_transporte BOOLEAN DEFAULT TRUE,
    jornada_laboral ENUM('Diurna', 'Nocturna', 'Mixta') DEFAULT 'Diurna',
    tipo_salario ENUM('Mensual', 'Quincenal', 'Semanal', 'Diario') DEFAULT 'Mensual',

    -- Información académica
    nivel_educativo ENUM('Ninguno', 'Primaria', 'Secundaria', 'Técnico', 'Tecnólogo', 'Profesional', 'Especialización', 'Maestría', 'Doctorado') DEFAULT 'Secundaria',
    titulo_profesional VARCHAR(255),
    institucion_educativa VARCHAR(255),

    -- Información de emergencia
    contacto_emergencia_nombre VARCHAR(100),
    contacto_emergencia_parentesco VARCHAR(50),
    contacto_emergencia_telefono VARCHAR(20),

    -- Información biométrica
    huella_digital LONGBLOB NULL,
    foto LONGBLOB NULL,
    foto_url VARCHAR(255) NULL,

    -- Estado y observaciones
    estado ENUM('Activo', 'Inactivo', 'Vacaciones', 'Incapacidad', 'Retirado') DEFAULT 'Activo',
    observaciones TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE SET NULL
);

-- =========================================
-- TABLAS DE INVENTARIO
-- =========================================

CREATE TABLE IF NOT EXISTS sedes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sede VARCHAR(100) NOT NULL UNIQUE,
    direccion VARCHAR(255),
    ciudad VARCHAR(100),
    departamento VARCHAR(100),
    telefono VARCHAR(20),
    email VARCHAR(100),
    responsable VARCHAR(100),
    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dispositivos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    dispositivos VARCHAR(100) NOT NULL UNIQUE,
    categoria ENUM('Tecnologia', 'Administrativo', 'Biomedico') DEFAULT 'Tecnologia',
    descripcion TEXT,
    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tipodisco (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tipodisco VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tiporam (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tram VARCHAR(100) NOT NULL UNIQUE,
    capacidad_gb INT,
    descripcion TEXT,
    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventario (
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_sede INT NOT NULL,
    id_dispositivo INT NOT NULL,
    id_tipodisco INT,
    id_tram INT,
    serial VARCHAR(100) UNIQUE NOT NULL,
    marca VARCHAR(100),
    modelo VARCHAR(100),
    procesador VARCHAR(100),
    ram VARCHAR(50),
    edisk VARCHAR(50),
    teclado VARCHAR(50),
    mouse VARCHAR(50),
    uautor VARCHAR(100),
    fechacreacion DATE,
    fechacompra DATE,
    fechabaja DATE NULL,
    estado ENUM('Activo', 'Baja', 'En reparacion', 'Prestamo', 'Extraviado') DEFAULT 'Activo',
    observaciones TEXT,
    imagen LONGBLOB NULL,
    imagen_url VARCHAR(255) NULL,
    qr_code VARCHAR(255) NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (id_sede) REFERENCES sedes(id),
    FOREIGN KEY (id_dispositivo) REFERENCES dispositivos(id),
    FOREIGN KEY (id_tipodisco) REFERENCES tipodisco(id),
    FOREIGN KEY (id_tram) REFERENCES tiporam(id)
);

-- =========================================
-- TABLAS DE TICKETS/MESA DE AYUDA
-- =========================================

CREATE TABLE IF NOT EXISTS categorias_ticket (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    color VARCHAR(7) DEFAULT '#007bff', -- Hex color
    icono VARCHAR(50) DEFAULT 'fas fa-question-circle',
    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
    orden INT DEFAULT 0,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prioridades_ticket (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    color VARCHAR(7) DEFAULT '#6c757d',
    nivel INT DEFAULT 1, -- 1=Baja, 2=Media, 3=Alta, 4=Urgente
    tiempo_respuesta_horas INT DEFAULT 24,
    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar prioridades por defecto
INSERT INTO prioridades_ticket (nombre, descripcion, color, nivel, tiempo_respuesta_horas) VALUES
('Baja', 'Solicitud no urgente', '#6c757d', 1, 72),
('Media', 'Solicitud con importancia media', '#ffc107', 2, 24),
('Alta', 'Solicitud importante que requiere atención', '#fd7e14', 3, 8),
('Urgente', 'Solicitud crítica que requiere atención inmediata', '#dc3545', 4, 2);

CREATE TABLE IF NOT EXISTS estados_ticket (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    color VARCHAR(7) DEFAULT '#007bff',
    es_final BOOLEAN DEFAULT FALSE, -- Si es estado final (Cerrado, Resuelto, etc.)
    orden INT DEFAULT 0,
    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar estados por defecto
INSERT INTO estados_ticket (nombre, descripcion, color, es_final, orden) VALUES
('Abierto', 'Ticket recién creado', '#007bff', FALSE, 1),
('En Progreso', 'Ticket siendo atendido', '#ffc107', FALSE, 2),
('Pendiente', 'Esperando respuesta del usuario', '#fd7e14', FALSE, 3),
('Resuelto', 'Ticket solucionado', '#28a745', TRUE, 4),
('Cerrado', 'Ticket cerrado', '#6c757d', TRUE, 5),
('Cancelado', 'Ticket cancelado', '#dc3545', TRUE, 6);

CREATE TABLE IF NOT EXISTS tickets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    numero_ticket VARCHAR(20) UNIQUE NOT NULL, -- Formato: TCK-2025-000001
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT NOT NULL,
    id_categoria INT,
    id_prioridad INT DEFAULT 1,
    id_estado INT DEFAULT 1,
    id_solicitante INT NOT NULL,
    id_asignado INT NULL,
    id_sede INT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    fecha_limite TIMESTAMP NULL,
    fecha_cierre TIMESTAMP NULL,
    tiempo_respuesta TIMESTAMP NULL,
    tiempo_resolucion TIMESTAMP NULL,
    calificacion INT NULL CHECK (calificacion >= 1 AND calificacion <= 5),
    comentario_cierre TEXT,
    es_privado BOOLEAN DEFAULT FALSE,
    etiquetas JSON NULL, -- Array de etiquetas
    campos_personalizados JSON NULL, -- Campos dinámicos
    archivos_adjuntos JSON NULL, -- Array de archivos

    FOREIGN KEY (id_categoria) REFERENCES categorias_ticket(id),
    FOREIGN KEY (id_prioridad) REFERENCES prioridades_ticket(id),
    FOREIGN KEY (id_estado) REFERENCES estados_ticket(id),
    FOREIGN KEY (id_solicitante) REFERENCES usuarios(id),
    FOREIGN KEY (id_asignado) REFERENCES usuarios(id),
    FOREIGN KEY (id_sede) REFERENCES sedes(id)
);

-- Historial de cambios en tickets
CREATE TABLE IF NOT EXISTS ticket_historial (
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_ticket INT NOT NULL,
    id_usuario INT NOT NULL,
    accion VARCHAR(100) NOT NULL, -- 'creado', 'actualizado', 'comentado', 'asignado', etc.
    descripcion TEXT,
    cambios JSON NULL, -- Cambios realizados en formato JSON
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_ticket) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);

-- Comentarios en tickets
CREATE TABLE IF NOT EXISTS ticket_comentarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_ticket INT NOT NULL,
    id_usuario INT NOT NULL,
    comentario TEXT NOT NULL,
    es_privado BOOLEAN DEFAULT FALSE,
    archivos_adjuntos JSON NULL,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_ticket) REFERENCES tickets(id) ON DELETE CASCADE,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);

-- =========================================
-- TABLAS DE GESTIÓN DOCUMENTAL
-- =========================================

CREATE TABLE IF NOT EXISTS tipos_documento (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    extensiones_permitidas VARCHAR(255) DEFAULT 'pdf,doc,docx,xls,xlsx,ppt,pptx,txt,jpg,jpeg,png',
    tamano_maximo_mb INT DEFAULT 10,
    requiere_aprobacion BOOLEAN DEFAULT FALSE,
    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documentos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    numero_documento VARCHAR(50) UNIQUE NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    id_tipo_documento INT NOT NULL,
    id_autor INT NOT NULL,
    id_aprobador INT NULL,
    id_sede INT,
    ruta_archivo VARCHAR(500) NOT NULL,
    nombre_archivo_original VARCHAR(255) NOT NULL,
    tamano_bytes BIGINT NOT NULL,
    extension VARCHAR(10) NOT NULL,
    hash_archivo VARCHAR(128) NOT NULL, -- SHA-256 del archivo
    version VARCHAR(20) DEFAULT '1.0',
    estado ENUM('borrador', 'pendiente_aprobacion', 'aprobado', 'rechazado', 'obsoleto') DEFAULT 'borrador',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_aprobacion TIMESTAMP NULL,
    fecha_expiracion DATE NULL,
    metadata JSON NULL, -- Metadatos adicionales
    palabras_clave VARCHAR(500), -- Para búsqueda
    acceso_publico BOOLEAN DEFAULT FALSE,

    FOREIGN KEY (id_tipo_documento) REFERENCES tipos_documento(id),
    FOREIGN KEY (id_autor) REFERENCES usuarios(id),
    FOREIGN KEY (id_aprobador) REFERENCES usuarios(id),
    FOREIGN KEY (id_sede) REFERENCES sedes(id)
);

-- Versiones de documentos
CREATE TABLE IF NOT EXISTS documento_versiones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_documento INT NOT NULL,
    version VARCHAR(20) NOT NULL,
    ruta_archivo VARCHAR(500) NOT NULL,
    nombre_archivo_original VARCHAR(255) NOT NULL,
    tamano_bytes BIGINT NOT NULL,
    hash_archivo VARCHAR(128) NOT NULL,
    cambios TEXT,
    id_autor INT NOT NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_documento) REFERENCES documentos(id) ON DELETE CASCADE,
    FOREIGN KEY (id_autor) REFERENCES usuarios(id)
);

-- =========================================
-- TABLAS DE FACTURAS Y COMPRAS
-- =========================================

CREATE TABLE IF NOT EXISTS proveedores (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nit VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    tipo_persona ENUM('natural', 'juridica') DEFAULT 'juridica',
    email VARCHAR(100),
    telefono VARCHAR(20),
    celular VARCHAR(20),
    direccion VARCHAR(255),
    ciudad VARCHAR(100),
    departamento VARCHAR(100),
    pais VARCHAR(100) DEFAULT 'Colombia',
    contacto_principal VARCHAR(100),
    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS facturas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    numero_factura VARCHAR(50) UNIQUE NOT NULL,
    id_proveedor INT NOT NULL,
    fecha_emision DATE NOT NULL,
    fecha_vencimiento DATE NULL,
    fecha_recepcion DATE DEFAULT CURRENT_DATE,
    subtotal DECIMAL(15,2) NOT NULL,
    iva DECIMAL(15,2) DEFAULT 0,
    retefuente DECIMAL(15,2) DEFAULT 0,
    reteica DECIMAL(15,2) DEFAULT 0,
    reteiva DECIMAL(15,2) DEFAULT 0,
    total DECIMAL(15,2) NOT NULL,
    moneda VARCHAR(3) DEFAULT 'COP',
    estado ENUM('pendiente', 'pagada', 'vencida', 'anulada') DEFAULT 'pendiente',
    observaciones TEXT,
    ruta_pdf VARCHAR(500) NULL,
    id_usuario_creacion INT NOT NULL,
    id_usuario_aprobacion INT NULL,
    fecha_aprobacion TIMESTAMP NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (id_proveedor) REFERENCES proveedores(id),
    FOREIGN KEY (id_usuario_creacion) REFERENCES usuarios(id),
    FOREIGN KEY (id_usuario_aprobacion) REFERENCES usuarios(id)
);

-- Detalles de facturas
CREATE TABLE IF NOT EXISTS factura_detalles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_factura INT NOT NULL,
    descripcion VARCHAR(255) NOT NULL,
    cantidad DECIMAL(10,2) NOT NULL,
    valor_unitario DECIMAL(15,2) NOT NULL,
    valor_total DECIMAL(15,2) NOT NULL,
    id_inventario INT NULL, -- Si está relacionado con un activo

    FOREIGN KEY (id_factura) REFERENCES facturas(id) ON DELETE CASCADE,
    FOREIGN KEY (id_inventario) REFERENCES inventario(id)
);

-- =========================================
-- TABLAS DE BIOMÉTRICO Y ASISTENCIA
-- =========================================

CREATE TABLE IF NOT EXISTS dispositivos_biometricos (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    ip_address VARCHAR(15) NOT NULL UNIQUE,
    puerto INT DEFAULT 4370,
    tipo ENUM('zkteco', 'hikvision', 'suprema', 'otros') DEFAULT 'zkteco',
    ubicacion VARCHAR(255),
    estado ENUM('activo', 'inactivo', 'mantenimiento') DEFAULT 'activo',
    ultima_sincronizacion TIMESTAMP NULL,
    configuracion JSON NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS registros_asistencia (
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_empleado INT NOT NULL,
    id_dispositivo INT NOT NULL,
    tipo_registro ENUM('entrada', 'salida', 'entrada_almuerzo', 'salida_almuerzo') DEFAULT 'entrada',
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modo_verificacion ENUM('huella', 'tarjeta', 'password', 'facial') DEFAULT 'huella',
    temperatura DECIMAL(4,1) NULL, -- Para medición de temperatura
    ubicacion_gps VARCHAR(100) NULL,
    estado ENUM('valido', 'duplicado', 'fuera_horario', 'anulado') DEFAULT 'valido',
    observaciones TEXT,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (id_empleado) REFERENCES empleados(id),
    FOREIGN KEY (id_dispositivo) REFERENCES dispositivos_biometricos(id)
);

-- =========================================
-- TABLAS DE WHATSAPP Y COMUNICACIONES
-- =========================================

CREATE TABLE IF NOT EXISTS whatsapp_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    api_url VARCHAR(255) NOT NULL,
    token VARCHAR(255) NOT NULL,
    numero_origen VARCHAR(20) NOT NULL,
    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
    configuracion JSON NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS whatsapp_mensajes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    numero_destino VARCHAR(20) NOT NULL,
    mensaje TEXT NOT NULL,
    tipo ENUM('texto', 'imagen', 'documento', 'audio', 'video') DEFAULT 'texto',
    id_usuario INT NULL,
    estado ENUM('enviado', 'entregado', 'leido', 'fallido') DEFAULT 'enviado',
    mensaje_id_externo VARCHAR(255) NULL,
    respuesta_ia BOOLEAN DEFAULT FALSE,
    metadata JSON NULL,
    fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega TIMESTAMP NULL,
    fecha_lectura TIMESTAMP NULL,

    FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);

-- =========================================
-- TABLAS DE LOGS Y AUDITORÍA
-- =========================================

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INT NULL,
    username VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(128),

    INDEX idx_timestamp (timestamp),
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_ip (ip_address)
);

CREATE TABLE IF NOT EXISTS system_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level ENUM('emergency', 'alert', 'critical', 'error', 'warning', 'notice', 'info', 'debug') DEFAULT 'info',
    message TEXT NOT NULL,
    context JSON NULL,
    file VARCHAR(255),
    line INT,
    trace TEXT,

    INDEX idx_timestamp (timestamp),
    INDEX idx_level (level)
);

-- =========================================
-- TABLAS DE LICENCIAS Y CERTIFICADOS
-- =========================================

CREATE TABLE IF NOT EXISTS tipos_licencia (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    dias_maximos INT DEFAULT 30,
    requiere_aprobacion BOOLEAN DEFAULT TRUE,
    estado ENUM('activo', 'inactivo') DEFAULT 'activo',
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar tipos de licencia por defecto
INSERT INTO tipos_licencia (nombre, descripcion, dias_maximos, requiere_aprobacion) VALUES
('Vacaciones', 'Licencia por vacaciones anuales', 30, TRUE),
('Enfermedad', 'Licencia por enfermedad', 365, TRUE),
('Maternidad/Paternidad', 'Licencia por maternidad o paternidad', 126, TRUE),
('Calamidad doméstica', 'Licencia por calamidad doméstica', 3, TRUE),
('Asuntos personales', 'Licencia por asuntos personales', 3, TRUE),
('Cita médica', 'Licencia por cita médica', 1, FALSE),
('Otro', 'Otro tipo de licencia', 30, TRUE);

CREATE TABLE IF NOT EXISTS licencias (
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_empleado INT NOT NULL,
    id_tipo_licencia INT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    dias_solicitados INT NOT NULL,
    motivo TEXT,
    id_aprobador INT NULL,
    estado ENUM('pendiente', 'aprobada', 'rechazada', 'cancelada') DEFAULT 'pendiente',
    observaciones TEXT,
    fecha_aprobacion TIMESTAMP NULL,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (id_empleado) REFERENCES empleados(id),
    FOREIGN KEY (id_tipo_licencia) REFERENCES tipos_licencia(id),
    FOREIGN KEY (id_aprobador) REFERENCES usuarios(id)
);

-- =========================================
-- TABLAS DE FLUJOS DE TRABAJO
-- =========================================

CREATE TABLE IF NOT EXISTS flujos_trabajo (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo ENUM('aprobacion', 'revision', 'notificacion', 'tarea') DEFAULT 'aprobacion',
    activo BOOLEAN DEFAULT TRUE,
    pasos JSON NOT NULL, -- Array de pasos del flujo
    condiciones JSON NULL, -- Condiciones para activar el flujo
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS instancias_flujo (
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_flujo INT NOT NULL,
    id_iniciador INT NOT NULL,
    id_referencia INT NULL, -- ID del registro relacionado (ticket, documento, etc.)
    tabla_referencia VARCHAR(50) NULL, -- Nombre de la tabla relacionada
    estado ENUM('activo', 'completado', 'cancelado') DEFAULT 'activo',
    paso_actual INT DEFAULT 1,
    datos JSON NULL, -- Datos del flujo
    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP NULL,

    FOREIGN KEY (id_flujo) REFERENCES flujos_trabajo(id),
    FOREIGN KEY (id_iniciador) REFERENCES usuarios(id)
);

-- =========================================
-- TABLAS DE REPORTES Y DASHBOARDS
-- =========================================

CREATE TABLE IF NOT EXISTS reportes_guardados (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    id_usuario INT NOT NULL,
    tipo ENUM('inventario', 'tickets', 'empleados', 'facturas', 'asistencia') NOT NULL,
    filtros JSON NOT NULL,
    columnas JSON NOT NULL,
    ordenamiento JSON NULL,
    publico BOOLEAN DEFAULT FALSE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultima_ejecucion TIMESTAMP NULL,

    FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
);

-- =========================================
-- TABLAS DE NOTIFICACIONES
-- =========================================

CREATE TABLE IF NOT EXISTS notificaciones (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    mensaje TEXT NOT NULL,
    tipo ENUM('info', 'success', 'warning', 'error') DEFAULT 'info',
    leida BOOLEAN DEFAULT FALSE,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_lectura TIMESTAMP NULL,
    enlace VARCHAR(500) NULL,
    datos JSON NULL,

    FOREIGN KEY (id_usuario) REFERENCES usuarios(id),
    INDEX idx_usuario_leida (id_usuario, leida),
    INDEX idx_fecha (fecha_creacion)
);

-- =========================================
-- TABLAS TEMPORALES Y UTILIDADES
-- =========================================

CREATE TABLE IF NOT EXISTS temp_codes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    code VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    INDEX idx_expires (expires_at)
);

-- =========================================
-- ÍNDICES ADICIONALES PARA PERFORMANCE
-- =========================================

-- Índices para inventario
CREATE INDEX idx_inventario_serial ON inventario(serial);
CREATE INDEX idx_inventario_estado ON inventario(estado);
CREATE INDEX idx_inventario_sede ON inventario(id_sede);
CREATE INDEX idx_inventario_dispositivo ON inventario(id_dispositivo);

-- Índices para tickets
CREATE INDEX idx_tickets_numero ON tickets(numero_ticket);
CREATE INDEX idx_tickets_estado ON tickets(id_estado);
CREATE INDEX idx_tickets_prioridad ON tickets(id_prioridad);
CREATE INDEX idx_tickets_solicitante ON tickets(id_solicitante);
CREATE INDEX idx_tickets_asignado ON tickets(id_asignado);
CREATE INDEX idx_tickets_fecha_creacion ON tickets(fecha_creacion);

-- Índices para empleados
CREATE INDEX idx_empleados_identificacion ON empleados(numero_identificacion);
CREATE INDEX idx_empleados_estado ON empleados(estado);
CREATE INDEX idx_empleados_departamento ON empleados(departamento_laboral);

-- Índices para logs
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);

-- =========================================
-- VISTAS ÚTILES
-- =========================================

-- Vista de inventario completo
CREATE OR REPLACE VIEW vista_inventario_completo AS
SELECT
    i.id,
    s.sede,
    d.dispositivos,
    td.tipodisco,
    tr.tram,
    i.serial,
    i.marca,
    i.modelo,
    i.procesador,
    i.ram,
    i.edisk,
    i.teclado,
    i.mouse,
    i.uautor,
    i.fechacreacion,
    i.fechacompra,
    i.fechabaja,
    i.estado,
    i.observaciones,
    i.fecha_creacion,
    i.fecha_actualizacion
FROM inventario i
LEFT JOIN sedes s ON i.id_sede = s.id
LEFT JOIN dispositivos d ON i.id_dispositivo = d.id
LEFT JOIN tipodisco td ON i.id_tipodisco = td.id
LEFT JOIN tiporam tr ON i.id_tram = tr.id;

-- Vista de tickets con información relacionada
CREATE OR REPLACE VIEW vista_tickets_completa AS
SELECT
    t.id,
    t.numero_ticket,
    t.titulo,
    t.descripcion,
    ct.nombre as categoria,
    pt.nombre as prioridad,
    et.nombre as estado,
    u1.nombreUsuario as solicitante,
    u2.nombreUsuario as asignado,
    s.sede,
    t.fecha_creacion,
    t.fecha_actualizacion,
    t.fecha_limite,
    t.fecha_cierre,
    t.calificacion
FROM tickets t
LEFT JOIN categorias_ticket ct ON t.id_categoria = ct.id
LEFT JOIN prioridades_ticket pt ON t.id_prioridad = pt.id
LEFT JOIN estados_ticket et ON t.id_estado = et.id
LEFT JOIN usuarios u1 ON t.id_solicitante = u1.id
LEFT JOIN usuarios u2 ON t.id_asignado = u2.id
LEFT JOIN sedes s ON t.id_sede = s.id;

-- Vista de empleados completa
CREATE OR REPLACE VIEW vista_empleados_completa AS
SELECT
    e.id,
    e.numero_identificacion,
    CONCAT(e.primer_nombre, ' ', COALESCE(e.segundo_nombre, ''), ' ', e.primer_apellido, ' ', COALESCE(e.segundo_apellido, '')) as nombre_completo,
    e.email_personal,
    e.celular_personal,
    e.cargo,
    e.departamento_laboral,
    e.fecha_ingreso,
    e.estado,
    u.nombreUsuario as usuario_sistema,
    u.email as email_sistema,
    u.estado as estado_sistema
FROM empleados e
LEFT JOIN usuarios u ON e.id_usuario = u.id;

-- =========================================
-- TRIGGERS PARA AUDITORÍA AUTOMÁTICA
-- =========================================

-- Trigger para auditar cambios en usuarios
DELIMITER ;;

CREATE TRIGGER audit_usuarios_update AFTER UPDATE ON usuarios
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (user_id, username, action, details, ip_address)
    VALUES (
        NEW.id,
        NEW.nombreUsuario,
        'usuario_actualizado',
        JSON_OBJECT(
            'old_data', JSON_OBJECT(
                'nombre', OLD.nombre,
                'email', OLD.email,
                'rol', OLD.rol,
                'estado', OLD.estado
            ),
            'new_data', JSON_OBJECT(
                'nombre', NEW.nombre,
                'email', NEW.email,
                'rol', NEW.rol,
                'estado', NEW.estado
            )
        ),
        @client_ip
    );
END;;

-- Trigger para auditar creación de tickets
CREATE TRIGGER audit_tickets_insert AFTER INSERT ON tickets
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (user_id, username, action, details, ip_address)
    VALUES (
        NEW.id_solicitante,
        (SELECT nombreUsuario FROM usuarios WHERE id = NEW.id_solicitante),
        'ticket_creado',
        JSON_OBJECT(
            'numero_ticket', NEW.numero_ticket,
            'titulo', NEW.titulo,
            'prioridad', (SELECT nombre FROM prioridades_ticket WHERE id = NEW.id_prioridad)
        ),
        @client_ip
    );
END;;

-- Trigger para auditar cambios de estado en tickets
CREATE TRIGGER audit_tickets_status_update AFTER UPDATE ON tickets
FOR EACH ROW
BEGIN
    IF OLD.id_estado != NEW.id_estado THEN
        INSERT INTO audit_log (user_id, username, action, details, ip_address)
        VALUES (
            NEW.id_asignado,
            COALESCE((SELECT nombreUsuario FROM usuarios WHERE id = NEW.id_asignado), 'Sistema'),
            'ticket_estado_cambiado',
            JSON_OBJECT(
                'numero_ticket', NEW.numero_ticket,
                'estado_anterior', (SELECT nombre FROM estados_ticket WHERE id = OLD.id_estado),
                'estado_nuevo', (SELECT nombre FROM estados_ticket WHERE id = NEW.id_estado)
            ),
            @client_ip
        );
    END IF;
END;;

DELIMITER ;

-- =========================================
-- DATOS DE PRUEBA Y CONFIGURACIÓN INICIAL
-- =========================================

-- Insertar sedes de ejemplo
INSERT INTO sedes (sede, direccion, ciudad, departamento, telefono, email, responsable) VALUES
('Sede Principal', 'Calle 123 #45-67', 'Bogotá', 'Cundinamarca', '6012345678', 'principal@empresa.com', 'Juan Pérez'),
('Sede Norte', 'Carrera 89 #12-34', 'Bogotá', 'Cundinamarca', '6012345679', 'norte@empresa.com', 'María González'),
('Sede Sur', 'Avenida 56 #78-90', 'Bogotá', 'Cundinamarca', '6012345680', 'sur@empresa.com', 'Carlos Rodríguez');

-- Insertar dispositivos de ejemplo
INSERT INTO dispositivos (dispositivos, categoria, descripcion) VALUES
('Computador Portátil', 'Tecnologia', 'Laptop para uso general'),
('Computador de Escritorio', 'Tecnologia', 'PC de escritorio'),
('Servidor', 'Tecnologia', 'Servidor de datos'),
('Impresora', 'Tecnologia', 'Impresora multifuncional'),
('Teléfono IP', 'Tecnologia', 'Teléfono VoIP'),
('Escritorio', 'Administrativo', 'Mueble de oficina'),
('Silla ergonómica', 'Administrativo', 'Silla para oficina'),
('Monitor', 'Tecnologia', 'Monitor LCD'),
('Teclado', 'Tecnologia', 'Teclado USB'),
('Mouse', 'Tecnologia', 'Mouse óptico');

-- Insertar tipos de disco
INSERT INTO tipodisco (tipodisco, descripcion) VALUES
('HDD 500GB', 'Disco duro mecánico 500GB'),
('SSD 256GB', 'Disco sólido 256GB'),
('SSD 512GB', 'Disco sólido 512GB'),
('SSD 1TB', 'Disco sólido 1TB'),
('NVMe 512GB', 'Disco NVMe 512GB'),
('No aplica', 'Sin disco duro');

-- Insertar tipos de RAM
INSERT INTO tiporam (tram, capacidad_gb, descripcion) VALUES
('4GB DDR3', 4, 'Memoria RAM DDR3 4GB'),
('8GB DDR3', 8, 'Memoria RAM DDR3 8GB'),
('16GB DDR4', 16, 'Memoria RAM DDR4 16GB'),
('32GB DDR4', 32, 'Memoria RAM DDR4 32GB'),
('No aplica', NULL, 'Sin memoria RAM');
