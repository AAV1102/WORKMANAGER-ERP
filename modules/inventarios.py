from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import os
from datetime import datetime, timezone

inventarios_bp = Blueprint('inventarios', __name__, template_folder='../templates')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "workmanager_erp.db")

def get_connection():
    """Returna conexión con row_factory lista para dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

SEDE_LABELS = {
    1: 'Sede Principal Bogota',
    2: 'Sede Norte Bogota',
    3: 'Sede Sur Bogota',
    4: 'Medellin',
    5: 'Sede Cali',
    6: 'Sede Barranquilla',
    7: 'Sede Cartagena',
    8: 'Sede Bucaramanga',
    9: 'Sede Pereira',
    10: 'Sede Manizales',
    11: 'Sede Ibague',
    12: 'Sede Villavicencio',
    13: 'Sede Neiva',
}

GENERAL_COLUMNS = [
    {"key": "serial", "label": "Serial"},
    {"key": "codigo_unificado", "label": "Codigo Unificado"},
    {"key": "placa", "label": "Placa"},
    {"key": "anterior_placa", "label": "Anterior Placa"},
    {"key": "sede", "label": "Sede"},
    {"key": "ip_sede", "label": "IP Sede"},
    {"key": "tecnologia", "label": "Tecnologia"},
    {"key": "marca", "label": "Marca"},
    {"key": "modelo", "label": "Modelo"},
    {"key": "mac", "label": "MAC"},
    {"key": "so", "label": "Sistema Operativo"},
    {"key": "hostname", "label": "Hostname"},
    {"key": "ip", "label": "IP Equipo"},
    {"key": "marca_modelo_telemedicina", "label": "Marca/Modelo Telemedicina"},
    {"key": "mouse", "label": "Mouse"},
    {"key": "teclado", "label": "Teclado"},
    {"key": "anterior_asignado", "label": "Anterior Asignado"},
    {"key": "asignado_a", "label": "Asignado A"},
    {"key": "cargo", "label": "Cargo"},
    {"key": "area", "label": "Area"},
    {"key": "contacto", "label": "Contacto"},
    {"key": "fecha_asignacion", "label": "Fecha Asignacion"},
    {"key": "cargado_nit", "label": "Cargado NIT"},
    {"key": "enviado_nit", "label": "Enviado NIT"},
    {"key": "fecha_enviado", "label": "Fecha Enviado"},
    {"key": "guia", "label": "Guia"},
    {"key": "procesador", "label": "Procesador"},
    {"key": "arquitectura_ram", "label": "Arquitectura RAM"},
    {"key": "cantidad_ram", "label": "Cantidad RAM"},
    {"key": "tipo_disco", "label": "Tipo de Disco"},
    {"key": "almacenamiento", "label": "Almacenamiento"},
    {"key": "placa_monitor", "label": "Placa Monitor"},
    {"key": "serial_monitor", "label": "Serial Monitor"},
    {"key": "marca_monitor", "label": "Marca Monitor"},
    {"key": "modelo_monitor", "label": "Modelo Monitor"},
    {"key": "estado", "label": "Estado"},
    {"key": "disponible", "label": "Disponible"},
    {"key": "observaciones", "label": "Observaciones"},
    {"key": "serial_telemedicina", "label": "Serial Telemedicina"},
    {"key": "tipo_componente_adicional", "label": "Tipo Componente Adicional"},
    {"key": "marca_modelo_componente_adicional", "label": "Marca/Modelo Componente"},
    {"key": "serial_componente_adicional", "label": "Serial Componente"},
    {"key": "marca_modelo_telefono", "label": "Marca/Modelo Telefono"},
    {"key": "serial_telefono", "label": "Serial Telefono"},
    {"key": "imei_telefono", "label": "IMEI Telefono"},
    {"key": "marca_modelo_impresora", "label": "Marca/Modelo Impresora"},
    {"key": "ip_impresora", "label": "IP Impresora"},
    {"key": "serial_impresora", "label": "Serial Impresora"},
    {"key": "pin_impresora", "label": "PIN Impresora"},
    {"key": "marca_modelo_cctv", "label": "Marca/Modelo CCTV"},
    {"key": "serial_cctv", "label": "Serial CCTV"},
    {"key": "entrada_oc_compra", "label": "Entrada OC Compra"},
    {"key": "fecha_llegada", "label": "Fecha de Llegada"},
    {"key": "oc", "label": "OC"},
    {"key": "proveedor", "label": "Proveedor"},
    {"key": "mueble_asignado", "label": "Mueble Asignado"},
]

BASE_FIELD_GROUPS = [
    "general_info",
    "assignment_info",
    "procurement_info",
    "logistics_info",
    "status_info",
]

TECHNOLOGY_OPTIONS = [
    "PC Escritorio",
    "Todo en Uno",
    "Portatil",
    "Portatiles",
    "Monitor",
    "Switch",
    "Switches",
    "Switch PoE",
    "Firewall Sophos",
    "Firewall",
    "Router",
    "Routers",
    "POS",
    "Camara PC",
    "Camaras PC",
    "Impresora",
    "Impresoras",
    "Impresora Etiquetas",
    "Telefono Fijo",
    "Telefonos Fijos",
    "Telefono Corporativo",
    "Telefonos Corporativos",
    "Celular",
    "Celulares",
    "Servidor",
    "Servidores",
    "UPS",
    "Regulador",
    "Reguladores",
    "Access Point",
    "Camara CCTV",
    "Camaras CCTV",
    "Telemedicina",
    "Cisco",
    "Mikrotik",
    "Microtik",
    "Mouse",
    "Teclado",
    "Base Portatil",
    "Bases Portatiles",
    "Adaptador de Red",
    "Adaptadores de Red",
    "Componente Adicional",
    "Componentes Adicionales",
    "Tablet",
    "Scanner"
]

TECHNOLOGY_FIELD_GROUPS = {
    "PC Escritorio": ["hardware_specs", "network_info", "monitor_info", "peripherals_info", "component_info", "telephony_info", "printer_info", "cctv_info", "telemedicina_info"],
    "Todo en Uno": ["hardware_specs", "network_info", "monitor_info", "peripherals_info", "component_info", "printer_info"],
    "Portatil": ["hardware_specs", "network_info", "peripherals_info", "component_info", "telephony_info"],
    "Monitor": ["monitor_info"],
    "Switch": ["network_info"],
    "Switch PoE": ["network_info"],
    "Firewall Sophos": ["network_info"],
    "Firewall": ["network_info"],
    "Router": ["network_info", "telephony_info"],
    "POS": ["hardware_specs", "network_info", "peripherals_info", "printer_info"],
    "Camara PC": ["peripherals_info", "telemedicina_info"],
    "Impresora": ["printer_info"],
    "Impresora Etiquetas": ["printer_info"],
    "Telefono Fijo": ["telephony_info"],
    "Telefono Corporativo": ["telephony_info"],
    "Celular": ["telephony_info"],
    "Servidor": ["hardware_specs", "network_info", "peripherals_info", "component_info", "telemedicina_info"],
    "UPS": ["hardware_specs"],
    "Regulador": ["hardware_specs"],
    "Access Point": ["network_info"],
    "Camara CCTV": ["cctv_info", "network_info"],
    "Telemedicina": ["telemedicina_info", "hardware_specs", "network_info", "peripherals_info", "component_info"],
    "Cisco": ["network_info", "telephony_info"],
    "Mikrotik": ["network_info"],
    "Mouse": ["peripherals_info"],
    "Teclado": ["peripherals_info"],
    "Base Portatil": ["peripherals_info"],
    "Adaptador de Red": ["network_info", "component_info"],
    "Componente Adicional": ["component_info"],
    "Tablet": ["hardware_specs", "network_info", "telephony_info"],
    "Scanner": ["hardware_specs", "peripherals_info"]
}

TECHNOLOGY_FIELD_GROUPS["Switches"] = TECHNOLOGY_FIELD_GROUPS["Switch"]
TECHNOLOGY_FIELD_GROUPS["Routers"] = TECHNOLOGY_FIELD_GROUPS["Router"]
TECHNOLOGY_FIELD_GROUPS["Camaras PC"] = TECHNOLOGY_FIELD_GROUPS["Camara PC"]
TECHNOLOGY_FIELD_GROUPS["Impresoras"] = TECHNOLOGY_FIELD_GROUPS["Impresora"]
TECHNOLOGY_FIELD_GROUPS["Telefonos Fijos"] = TECHNOLOGY_FIELD_GROUPS["Telefono Fijo"]
TECHNOLOGY_FIELD_GROUPS["Telefonos Corporativos"] = TECHNOLOGY_FIELD_GROUPS["Telefono Corporativo"]
TECHNOLOGY_FIELD_GROUPS["Celulares"] = TECHNOLOGY_FIELD_GROUPS["Celular"]
TECHNOLOGY_FIELD_GROUPS["Servidores"] = TECHNOLOGY_FIELD_GROUPS["Servidor"]
TECHNOLOGY_FIELD_GROUPS["Reguladores"] = TECHNOLOGY_FIELD_GROUPS["Regulador"]
TECHNOLOGY_FIELD_GROUPS["Camaras CCTV"] = TECHNOLOGY_FIELD_GROUPS["Camara CCTV"]
TECHNOLOGY_FIELD_GROUPS["Microtik"] = TECHNOLOGY_FIELD_GROUPS["Mikrotik"]
TECHNOLOGY_FIELD_GROUPS["Bases Portatiles"] = TECHNOLOGY_FIELD_GROUPS["Base Portatil"]
TECHNOLOGY_FIELD_GROUPS["Portatiles"] = TECHNOLOGY_FIELD_GROUPS["Portatil"]
TECHNOLOGY_FIELD_GROUPS["Adaptadores de Red"] = TECHNOLOGY_FIELD_GROUPS["Adaptador de Red"]
TECHNOLOGY_FIELD_GROUPS["Componentes Adicionales"] = TECHNOLOGY_FIELD_GROUPS["Componente Adicional"]

INDIVIDUAL_DB_COLUMNS = [
    "codigo_barras_individual",
    "codigo_unificado",
    "entrada_oc_compra",
    "cargado_nit",
    "enviado_nit",
    "ciudad",
    "tecnologia",
    "serial",
    "modelo",
    "anterior_asignado",
    "anterior_placa",
    "placa",
    "marca",
    "procesador",
    "arch_ram",
    "cantidad_ram",
    "tipo_disco",
    "espacio_disco",
    "so",
    "estado",
    "asignado_nuevo",
    "fecha",
    "fecha_llegada",
    "area",
    "marca_monitor",
    "modelo_monitor",
    "serial_monitor",
    "placa_monitor",
    "proveedor",
    "oc",
    "observaciones",
    "disponible",
    "sede_id",
    "ip_sede",
    "mac",
    "hostname",
    "ip",
    "marca_modelo_telemedicina",
    "serial_telemedicina",
    "mouse",
    "teclado",
    "cargo",
    "contacto",
    "fecha_enviado",
    "guia",
    "tipo_componente_adicional",
    "marca_modelo_componente_adicional",
    "serial_componente_adicional",
    "marca_modelo_telefono",
    "serial_telefono",
    "imei_telefono",
    "marca_modelo_impresora",
    "ip_impresora",
    "serial_impresora",
    "pin_impresora",
    "marca_modelo_cctv",
    "serial_cctv",
    "mueble_asignado",
    "creador_registro"
]

def get_sede_name(sede_id):
    # Accept None, empty string or invalid values gracefully
    if not sede_id:
        return 'Sin sede definida'
    try:
        return SEDE_LABELS.get(int(sede_id), 'Sin sede definida')
    except (TypeError, ValueError):
        return 'Sin sede definida'


def get_sedes_options():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, nombre, ciudad FROM sedes ORDER BY nombre")
    sedes = [dict(row) for row in c.fetchall()]
    conn.close()
    return sedes


def generar_codigo_individual(conn, sede_id, tecnologia):
    """
    Genera un código de barras individual único basado en la sede y la tecnología.
    Formato: [CODIGO_SEDE]-[CODIGO_TEC]-[CONSECUTIVO]
    Ejemplo: MED-MON-001
    """
    cur = conn.cursor()

    # 1. Obtener código de la sede (ej: MED para Medellín)
    cur.execute("SELECT codigo FROM sedes WHERE id = ? LIMIT 1", (sede_id,))
    sede_row = cur.fetchone()
    sede_code = sede_row['codigo'] if sede_row and sede_row['codigo'] else "GEN"

    # 2. Obtener código de la tecnología (ej: MON para Monitor)
    tec_code = "TEC"
    if tecnologia:
        # Tomar las primeras 3 letras y limpiar caracteres no alfanuméricos
        tec_code = ''.join(filter(str.isalnum, tecnologia))[:3].upper()

    # 3. Encontrar el último consecutivo para esta combinación
    prefix = f"{sede_code}-{tec_code}-"
    cur.execute("""
        SELECT codigo_barras_individual FROM equipos_individuales
        WHERE codigo_barras_individual LIKE ?
        ORDER BY codigo_barras_individual DESC
        LIMIT 1
    """, (f"{prefix}%",))
    last_code_row = cur.fetchone()

    last_num = 0
    if last_code_row:
        try:
            last_num = int(last_code_row['codigo_barras_individual'].split('-')[-1])
        except (ValueError, IndexError):
            last_num = 0

    return f"{prefix}{str(last_num + 1).zfill(3)}"

def generar_codigo_agrupado(conn, sede_id):
    """
    Genera un código de barras unificado para equipos agrupados por sede.
    Formato: [CODIGO_SEDE]-AGRU-[CONSECUTIVO]
    Ejemplo: MED-AGRU-001
    """
    cur = conn.cursor()
    cur.execute("SELECT codigo FROM sedes WHERE id = ? LIMIT 1", (sede_id,))
    sede_row = cur.fetchone()
    sede_code = sede_row['codigo'] if sede_row and sede_row['codigo'] else "GEN"

    prefix = f"{sede_code}-AGRU-"
    cur.execute(
        """
        SELECT codigo_barras_unificado FROM equipos_agrupados
        WHERE codigo_barras_unificado LIKE ?
        ORDER BY codigo_barras_unificado DESC
        LIMIT 1
        """,
        (f"{prefix}%",),
    )
    last_code_row = cur.fetchone()
    last_num = 0
    if last_code_row:
        try:
            last_num = int(last_code_row['codigo_barras_unificado'].split('-')[-1])
        except (ValueError, IndexError):
            last_num = 0
    return f"{prefix}{str(last_num + 1).zfill(3)}"

def build_individual_payload(form):
    data = {}
    for column in INDIVIDUAL_DB_COLUMNS:
        value = form.get(column)
        if isinstance(value, str):
            value = value.strip()
        data[column] = value or None

    if not data.get('estado'):
        data['estado'] = 'disponible'
    if not data.get('disponible'):
        data['disponible'] = 'Si'

    sede_value = data.get('sede_id')
    if sede_value:
        try:
            data['sede_id'] = int(sede_value)
        except ValueError:
            data['sede_id'] = None

    return data

def insert_individual_record_with_code(data):
    """Inserta un registro y genera el código si es necesario."""
    conn = get_connection()
    if not data.get('codigo_barras_individual'):
        data['codigo_barras_individual'] = generar_codigo_individual(conn, data.get('sede_id'), data.get('tecnologia'))
    
    insert_individual_record(data)
    conn.close()

def insert_individual_record(data):
    conn = get_connection()
    c = conn.cursor()
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    values = list(data.values())
    c.execute(
        f"""
        INSERT INTO equipos_individuales ({columns}, fecha_creacion)
        VALUES ({placeholders}, ?)
        """,
        values + [datetime.now(timezone.utc).isoformat(timespec='seconds')]
    )
    conn.commit()
    conn.close()


@inventarios_bp.route('/inventarios/api/generar_codigo', methods=['GET'])
def api_generar_codigo():
    """Genera un codigo individual basado en sede y tecnologia (uso en formulario)."""
    sede_id = request.args.get('sede_id')
    tecnologia = request.args.get('tecnologia')
    if not sede_id or not tecnologia:
        return jsonify({'error': 'Faltan parametros'}), 400
    conn = get_connection()
    try:
        codigo = generar_codigo_individual(conn, sede_id, tecnologia)
    finally:
        conn.close()
    return jsonify({'codigo': codigo})


def map_individual_row(row_dict):
    """Normaliza el row de equipos_individuales a las llaves visibles en UI/API."""
    return {
        "id": row_dict.get("id"),
        "serial": row_dict.get("serial"),
        "codigo_unificado": row_dict.get("codigo_unificado"),
        "codigo_individual": row_dict.get("codigo_barras_individual"),
        "placa": row_dict.get("placa"),
        "anterior_placa": row_dict.get("anterior_placa"),
        "sede": get_sede_name(row_dict.get("sede_id")),
        "ip_sede": row_dict.get("ip_sede"),
        "tecnologia": row_dict.get("tecnologia"),
        "marca": row_dict.get("marca"),
        "modelo": row_dict.get("modelo"),
        "mac": row_dict.get("mac"),
        "so": row_dict.get("so"),
        "hostname": row_dict.get("hostname"),
        "ip": row_dict.get("ip"),
        "marca_modelo_telemedicina": row_dict.get("marca_modelo_telemedicina"),
        "mouse": row_dict.get("mouse"),
        "teclado": row_dict.get("teclado"),
        "anterior_asignado": row_dict.get("anterior_asignado"),
        "asignado_a": row_dict.get("asignado_nuevo"),
        "cargo": row_dict.get("cargo"),
        "area": row_dict.get("area"),
        "contacto": row_dict.get("contacto"),
        "fecha_asignacion": row_dict.get("fecha"),
        "cargado_nit": row_dict.get("cargado_nit"),
        "enviado_nit": row_dict.get("enviado_nit"),
        "fecha_enviado": row_dict.get("fecha_enviado"),
        "guia": row_dict.get("guia"),
        "procesador": row_dict.get("procesador"),
        "arquitectura_ram": row_dict.get("arch_ram"),
        "cantidad_ram": row_dict.get("cantidad_ram"),
        "tipo_disco": row_dict.get("tipo_disco"),
        "almacenamiento": row_dict.get("espacio_disco"),
        "placa_monitor": row_dict.get("placa_monitor"),
        "serial_monitor": row_dict.get("serial_monitor"),
        "marca_monitor": row_dict.get("marca_monitor"),
        "modelo_monitor": row_dict.get("modelo_monitor"),
        "estado": row_dict.get("estado"),
        "disponible": row_dict.get("disponible"),
        "observaciones": row_dict.get("observaciones"),
        "serial_telemedicina": row_dict.get("serial_telemedicina"),
        "tipo_componente_adicional": row_dict.get("tipo_componente_adicional"),
        "marca_modelo_componente_adicional": row_dict.get("marca_modelo_componente_adicional"),
        "serial_componente_adicional": row_dict.get("serial_componente_adicional"),
        "marca_modelo_telefono": row_dict.get("marca_modelo_telefono"),
        "serial_telefono": row_dict.get("serial_telefono"),
        "imei_telefono": row_dict.get("imei_telefono"),
        "marca_modelo_impresora": row_dict.get("marca_modelo_impresora"),
        "ip_impresora": row_dict.get("ip_impresora"),
        "serial_impresora": row_dict.get("serial_impresora"),
        "pin_impresora": row_dict.get("pin_impresora"),
        "marca_modelo_cctv": row_dict.get("marca_modelo_cctv"),
        "serial_cctv": row_dict.get("serial_cctv"),
        "entrada_oc_compra": row_dict.get("entrada_oc_compra"),
        "fecha_llegada": row_dict.get("fecha_llegada"),
        "oc": row_dict.get("oc"),
        "proveedor": row_dict.get("proveedor"),
        "mueble_asignado": row_dict.get("mueble_asignado"),
        "fecha_creacion": row_dict.get("fecha_creacion"),
        "creador_registro": row_dict.get("creador_registro"),
    }

def normalize_inventory_item(row, item_type='individual'):
    """
    Toma una fila de cualquier tabla de inventario y la convierte a un formato estándar.
    Esta es la clave para tener una tabla limpia y organizada en el frontend.
    """
    row_dict = dict(row)
    if item_type == 'agrupado':
        return {
            "id": row_dict.get("id"),
            "tipo": "agrupado",
            "codigo": row_dict.get("codigo_barras_unificado"),
            "serial": "N/A (Agrupado)",
            "marca": row_dict.get("descripcion_general"),
            "modelo": "",
            "estado": row_dict.get("estado_general"),
            "asignado": row_dict.get("asignado_actual"),
            "sede": get_sede_name(row_dict.get("sede_id")),
        }
    # Por defecto, se asume 'individual' o similar
    return {
        "id": row_dict.get("id"),
        "tipo": "individual",
        "codigo": row_dict.get("codigo_barras_individual"),
        "serial": row_dict.get("serial"),
        "marca": row_dict.get("marca"),
        "modelo": row_dict.get("modelo"),
        "estado": row_dict.get("estado"),
        "asignado": row_dict.get("asignado_nuevo"),
        "sede": get_sede_name(row_dict.get("sede_id")),
    }

def normalize_inventory_item(row, item_type='individual'):
    """
    Toma una fila de cualquier tabla de inventario y la convierte a un formato estándar.
    Esta es la clave para tener una tabla limpia y organizada en el frontend.
    """
    row_dict = dict(row)
    if item_type == 'agrupado':
        return {
            "id": row_dict.get("id"),
            "tipo": "agrupado",
            "codigo": row_dict.get("codigo_barras_unificado"),
            "serial": "N/A (Agrupado)",
            "marca": row_dict.get("descripcion_general"),
            "modelo": "",
            "estado": row_dict.get("estado_general"),
            "asignado": row_dict.get("asignado_actual"),
            "sede": get_sede_name(row_dict.get("sede_id")),
        }
    # Por defecto, se asume 'individual' o similar
    return {
        "id": row_dict.get("id"),
        "tipo": "individual",
        "codigo": row_dict.get("codigo_barras_individual"),
        "serial": row_dict.get("serial"),
        "marca": row_dict.get("marca"),
        "modelo": row_dict.get("modelo"),
        "estado": row_dict.get("estado"),
        "asignado": row_dict.get("asignado_nuevo"),
        "sede": get_sede_name(row_dict.get("sede_id")),
    }

@inventarios_bp.route('/inventarios')
def inventarios():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Get grouped equipment with statistics
    c.execute("SELECT * FROM equipos_agrupados")
    equipos_agrupados = c.fetchall()

    # Calculate inventory statistics
    stats = {}
    try:
        # KPIs principales
        c.execute("SELECT COUNT(*) FROM equipos_individuales")
        stats['total_individual'] = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM equipos_agrupados")
        stats['total_grouped'] = c.fetchone()[0] or 0
        stats['total_equipment'] = stats['total_individual'] + stats['total_grouped']
        
        c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE LOWER(estado) = 'asignado'")
        stats['total_asignados'] = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM equipos_individuales WHERE LOWER(estado) = 'disponible'")
        stats['total_disponibles'] = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(DISTINCT id) FROM sedes")
        stats['total_sedes'] = c.fetchone()[0] or 0
    except Exception:
        stats = {k: 0 for k in ['total_individual', 'total_grouped', 'total_equipment', 'total_asignados', 'total_disponibles', 'total_sedes']}

    # Count by equipment type (assuming 'tecnologia' is the type)
    c.execute("SELECT tecnologia, COUNT(*) as count FROM equipos_individuales GROUP BY tecnologia")
    equipment_types = c.fetchall()
    stats['types'] = {row[0]: row[1] for row in equipment_types}

    # Total counts
    conn.close()
    return render_template(
        'inventarios.html',
        equipos_agrupados=equipos_agrupados,
        stats=stats,
        general_columns=GENERAL_COLUMNS,
        sede_labels=SEDE_LABELS,
    )

@inventarios_bp.route('/inventarios/api/dashboard', methods=['GET'])
def api_inventarios_dashboard():
    """
    Devuelve datasets listos para poblar las pestañas adicionales del inventario.
    Todo se alimenta de las tablas del inventario general (individual, agrupado, bajas y tandas).
    """
    conn = get_connection()
    c = conn.cursor()
    try:
        # Equipos agrupados (resumen)
        c.execute("""
            SELECT id, codigo_barras_unificado, descripcion_general, estado_general,
                   asignado_actual, sede_id, nit, observaciones, fecha_creacion
              FROM equipos_agrupados
             ORDER BY id DESC
        """)
        agrupados = [normalize_inventory_item(row, 'agrupado') for row in c.fetchall()]

        # Equipos individuales (resumen)
        c.execute("""
            SELECT id, codigo_barras_individual, codigo_unificado, serial, marca, modelo, tecnologia,
                   estado, asignado_nuevo, area, sede_id, observaciones
              FROM equipos_individuales
             ORDER BY id DESC
        """)
        individuales = [normalize_inventory_item(row) for row in c.fetchall()]

        # Resumen por sede
        c.execute("""
            SELECT ei.sede_id,
                   COUNT(*) as total,
                   SUM(CASE WHEN LOWER(COALESCE(ei.estado, '')) IN ('disponible','activo','nuevo','buen estado','bueno') THEN 1 ELSE 0 END) as disponibles,
                   SUM(CASE WHEN LOWER(COALESCE(ei.estado, '')) IN ('asignado','usado') OR (ei.asignado_nuevo IS NOT NULL AND TRIM(ei.asignado_nuevo) != '') THEN 1 ELSE 0 END) as asignados,
                   SUM(CASE WHEN LOWER(COALESCE(ei.estado, '')) LIKE 'baja%' OR LOWER(COALESCE(ei.estado,'')) = 'baja' THEN 1 ELSE 0 END) as bajas
              FROM equipos_individuales ei
             GROUP BY ei.sede_id
             ORDER BY total DESC
        """)
        por_sede = [
            {
                "sede": get_sede_name(row["sede_id"]),
                "total": row["total"],
                "disponibles": row["disponibles"],
                "asignados": row["asignados"],
                "bajas": row["bajas"],
            }
            for row in c.fetchall()
        ]

        # Resumen por usuario asignado
        c.execute("""
            SELECT TRIM(asignado_nuevo) as usuario,
                   COUNT(*) as total,
                   SUM(CASE WHEN LOWER(COALESCE(estado,'')) LIKE 'baja%' THEN 1 ELSE 0 END) as bajas,
                   SUM(CASE WHEN LOWER(COALESCE(estado,'')) IN ('asignado','activo','usado') THEN 1 ELSE 0 END) as activos
              FROM equipos_individuales
             WHERE asignado_nuevo IS NOT NULL AND TRIM(asignado_nuevo) != ''
             GROUP BY TRIM(asignado_nuevo)
             ORDER BY total DESC
             LIMIT 200
        """)
        por_usuario = [
            {
                "usuario": row["usuario"],
                "total": row["total"],
                "activos": row["activos"],
                "bajas": row["bajas"],
            }
            for row in c.fetchall()
        ]

        # Resumen por área
        c.execute("""
            SELECT TRIM(area) as area,
                   COUNT(*) as total,
                   SUM(CASE WHEN LOWER(COALESCE(estado,'')) LIKE 'baja%' THEN 1 ELSE 0 END) as bajas
              FROM equipos_individuales
             WHERE area IS NOT NULL AND TRIM(area) != ''
             GROUP BY TRIM(area)
             ORDER BY total DESC
        """)
        por_area = [
            {
                "area": row["area"],
                "total": row["total"],
                "bajas": row["bajas"],
            }
            for row in c.fetchall()
        ]

        def _map_with_sede(rows):
            data = []
            for row in rows:
                data.append({
                    "id": row["id"],
                    "codigo": row["codigo_barras_individual"],
                    "serial": row["serial"],
                    "marca": row["marca"],
                    "modelo": row["modelo"],
                    "tecnologia": row["tecnologia"],
                    "estado": row["estado"],
                    "asignado": row["asignado_nuevo"],
                    "sede": get_sede_name(row["sede_id"]),
                    "area": row["area"],
                    "observaciones": row["observaciones"],
                })
            return data

        # Categorías especiales
        c.execute("""
            SELECT id, codigo_barras_individual, serial, marca, modelo, tecnologia, estado, asignado_nuevo,
                   sede_id, area, observaciones
              FROM equipos_individuales
             WHERE LOWER(COALESCE(estado,'')) LIKE '%repot%'
                OR LOWER(COALESCE(observaciones,'')) LIKE '%repot%'
        """)
        repotenciados = _map_with_sede(c.fetchall())

        c.execute("""
            SELECT id, codigo_barras_individual, serial, marca, modelo, tecnologia, estado, asignado_nuevo,
                   sede_id, area, observaciones
              FROM equipos_individuales
             WHERE LOWER(COALESCE(estado,'')) LIKE '%prest%'
                OR LOWER(COALESCE(observaciones,'')) LIKE '%prest%'
        """)
        prestamos = _map_with_sede(c.fetchall())

        c.execute("""
            SELECT id, codigo_barras_individual, serial, marca, modelo, tecnologia, estado, asignado_nuevo,
                   sede_id, area, observaciones
              FROM equipos_individuales
             WHERE LOWER(COALESCE(tecnologia,'')) LIKE '%telemed%'
                OR LOWER(COALESCE(observaciones,'')) LIKE '%telemed%'
        """)
        telemedicina = _map_with_sede(c.fetchall())

        c.execute("""
            SELECT id, codigo_barras_individual, serial, marca, modelo, tecnologia, estado, asignado_nuevo,
                   sede_id, area, observaciones
              FROM equipos_individuales
             WHERE LOWER(COALESCE(tecnologia,'')) LIKE '%d2k%'
                OR LOWER(COALESCE(tecnologia,'')) LIKE '%dme%'
                OR LOWER(COALESCE(observaciones,'')) LIKE '%d2k%'
                OR LOWER(COALESCE(observaciones,'')) LIKE '%dme%'
        """)
        d2k_dme = _map_with_sede(c.fetchall())

        c.execute("""
            SELECT id, codigo_barras_individual, serial, marca, modelo, tecnologia, estado, asignado_nuevo,
                   sede_id, area, observaciones, tipo_componente_adicional,
                   marca_modelo_componente_adicional, serial_componente_adicional
              FROM equipos_individuales
             WHERE tipo_componente_adicional IS NOT NULL AND TRIM(tipo_componente_adicional) != ''
        """)
        componentes_adicionales = []
        for row in c.fetchall():
            componentes_adicionales.append({
                "id": row["id"],
                "codigo": row["codigo_barras_individual"],
                "serial": row["serial"],
                "marca": row["marca"],
                "modelo": row["modelo"],
                "tecnologia": row["tecnologia"],
                "estado": row["estado"],
                "asignado": row["asignado_nuevo"],
                "sede": get_sede_name(row["sede_id"]),
                "area": row["area"],
                "observaciones": row["observaciones"],
                "tipo_componente": row["tipo_componente_adicional"],
                "descripcion_componente": row["marca_modelo_componente_adicional"],
                "serial_componente": row["serial_componente_adicional"],
            })
        # Componentes adicionales de la tabla específica (si existe)
        try:
            c.execute("""
                SELECT ea.id, ea.codigo_barras_individual, ea.tipo_accesorio, ea.marca, ea.modelo,
                       ea.serial, ea.estado, ea.observaciones, ea.caracteristicas, ei.sede_id, ei.asignado_nuevo, ei.area
                  FROM equipos_adicionales ea
             LEFT JOIN equipos_individuales ei ON ei.id = ea.equipo_principal_id
            """)
            for row in c.fetchall():
                componentes_adicionales.append({
                    "id": row["id"],
                    "codigo": row["codigo_barras_individual"],
                    "serial": row["serial"],
                    "marca": row["marca"],
                    "modelo": row["modelo"],
                    "tecnologia": None,
                    "estado": row["estado"],
                    "asignado": row["asignado_nuevo"],
                    "sede": get_sede_name(row["sede_id"]),
                    "area": row["area"],
                    "observaciones": row["observaciones"],
                    "tipo_componente": row["tipo_accesorio"],
                    "descripcion_componente": row["caracteristicas"] or row["modelo"],
                    "serial_componente": row["serial"],
                })
        except sqlite3.OperationalError:
            pass

        # Totales por tecnología
        c.execute("""
            SELECT COALESCE(tecnologia, 'Sin tecnologia') as tecnologia,
                   COUNT(*) as total,
                   SUM(CASE WHEN LOWER(COALESCE(estado,'')) LIKE 'baja%' THEN 1 ELSE 0 END) as bajas,
                   SUM(CASE WHEN LOWER(COALESCE(estado,'')) IN ('disponible','activo','nuevo','buen estado','bueno') THEN 1 ELSE 0 END) as disponibles
              FROM equipos_individuales
             GROUP BY COALESCE(tecnologia, 'Sin tecnologia')
             ORDER BY total DESC
        """)
        tecnologias = [
            {
                "tecnologia": row["tecnologia"],
                "total": row["total"],
                "disponibles": row["disponibles"],
                "bajas": row["bajas"],
            }
            for row in c.fetchall()
        ]

        # Equipos asignados (individuales y agrupados)
        c.execute("""
            SELECT id, codigo_barras_individual, serial, marca, modelo, estado, asignado_nuevo,
                   sede_id, fecha, area
              FROM equipos_individuales
             WHERE (asignado_nuevo IS NOT NULL AND TRIM(asignado_nuevo) != '')
                OR LOWER(COALESCE(estado,'')) = 'asignado'
        """)
        asignados = [
            {
                "id": row["id"],
                "tipo": "individual",
                "codigo": row["codigo_barras_individual"],
                "serial": row["serial"],
                "marca": row["marca"],
                "modelo": row["modelo"],
                "estado": row["estado"],
                "usuario": row["asignado_nuevo"],
                "sede": get_sede_name(row["sede_id"]),
                "fecha": row["fecha"],
                "area": row["area"],
            }
            for row in c.fetchall()
        ]
        c.execute("""
            SELECT id, codigo_barras_unificado, descripcion_general, estado_general, asignado_actual,
                   sede_id, fecha_creacion
              FROM equipos_agrupados
             WHERE asignado_actual IS NOT NULL AND TRIM(asignado_actual) != ''
        """)
        for row in c.fetchall():
            asignados.append({
                "id": row["id"],
                "tipo": "agrupado",
                "codigo": row["codigo_barras_unificado"],
                "serial": None,
                "marca": row["descripcion_general"],
                "modelo": None,
                "estado": row["estado_general"],
                "usuario": row["asignado_actual"],
                "sede": get_sede_name(row["sede_id"]),
                "fecha": row["fecha_creacion"],
                "area": None,
            })

        # Equipos en baja
        c.execute("""
            SELECT ib.id as baja_id, ib.equipo_id, ib.tipo_inventario, ib.motivo_baja, ib.fecha_baja,
                   ib.responsable_baja, ib.observaciones,
                   ei.codigo_barras_individual AS codigo_individual,
                   ei.serial AS serial_individual,
                   ei.marca AS marca_individual,
                   ei.modelo AS modelo_individual,
                   ei.estado AS estado_individual,
                   ei.asignado_nuevo AS asignado_individual,
                   ei.sede_id AS sede_individual,
                   ea.codigo_barras_unificado AS codigo_agrupado,
                   ea.descripcion_general AS descripcion_agrupado,
                   ea.estado_general AS estado_agrupado,
                   ea.asignado_actual AS asignado_agrupado,
                   ea.sede_id AS sede_agrupado
              FROM inventario_bajas ib
         LEFT JOIN equipos_individuales ei ON ib.tipo_inventario = 'individual' AND ei.id = ib.equipo_id
         LEFT JOIN equipos_agrupados ea ON ib.tipo_inventario = 'agrupado' AND ea.id = ib.equipo_id
             ORDER BY ib.fecha_baja DESC
        """)
        bajas = []
        for row in c.fetchall():
            sede_id = row["sede_individual"] or row["sede_agrupado"]
            bajas.append({
                "id": row["baja_id"],
                "equipo_id": row["equipo_id"],
                "tipo": row["tipo_inventario"],
                "motivo": row["motivo_baja"],
                "fecha": row["fecha_baja"],
                "responsable": row["responsable_baja"],
                "observaciones": row["observaciones"],
                "codigo": row["codigo_individual"] or row["codigo_agrupado"],
                "serial": row["serial_individual"],
                "marca": row["marca_individual"] or row["descripcion_agrupado"],
                "modelo": row["modelo_individual"],
                "estado": row["estado_individual"] or row["estado_agrupado"],
                "asignado": row["asignado_individual"] or row["asignado_agrupado"],
                "sede": get_sede_name(sede_id),
            })

        # Tandas nuevas
        c.execute("""
            SELECT id, numero_tanda, descripcion, fecha_ingreso, cantidad_equipos, proveedor,
                   valor_total, estado, observaciones, created_at
              FROM tandas_equipos_nuevos
             ORDER BY fecha_ingreso DESC
        """)
        tandas = [dict(row) for row in c.fetchall()]

    finally:
        conn.close()

    return jsonify({
        "agrupados": agrupados,
        "individuales": individuales,
        "por_sede": por_sede,
        "por_usuario": por_usuario,
        "por_area": por_area,
        "repotenciados": repotenciados,
        "prestamos": prestamos,
        "telemedicina": telemedicina,
        "d2k_dme": d2k_dme,
        "componentes_adicionales": componentes_adicionales,
        "tecnologias": tecnologias,
        "asignados": asignados,
        "bajas": bajas,
        "tandas": tandas,
    })

@inventarios_bp.route('/inventarios/api/search/_all_')
def api_search_all():
    """API endpoint to get the consolidated inventory with all the requested headers."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT id, codigo_barras_unificado, nit, sede_id, asignado_anterior,
               asignado_actual, descripcion_general, estado_general,
               creador_registro, fecha_creacion, trazabilidad_soporte,
               documentos_entrega, observaciones
        FROM equipos_agrupados
    """)
    agrupados = c.fetchall()

    c.execute("SELECT * FROM equipos_individuales")
    individuales = c.fetchall()

    # Incluir equipos de la tabla 'inventario' (importador universal)
    inventario_items = []
    try:
        c.execute("""
            SELECT i.id, i.serial, i.marca, i.modelo, i.estado, i.observaciones,
                   i.uautor as asignado_a, i.fechacreacion as fecha_creacion,
                   s.sede as sede_nombre, d.dispositivos as tecnologia
            FROM inventario i
            LEFT JOIN sedes s ON i.id_sede = s.id
            LEFT JOIN dispositivos d ON i.id_dispositivo = d.id
        """)
        inventario_items = c.fetchall()
    except sqlite3.OperationalError:
        # La tabla "inventario" o "dispositivos" no existe; continuar sin esos registros
        inventario_items = []

    conn.close()

    results = []

    for row in agrupados:
        row_dict = dict(row)
        item = {
            "tipo": "agrupado",
            "id": row_dict.get("id"),
            "serial": None,
            "codigo_unificado": row_dict.get("codigo_barras_unificado"),
            "codigo_individual": None,
            "placa": None,
            "anterior_placa": None,
            "sede": get_sede_name(row_dict.get("sede_id")),
            "ip_sede": None,
            "tecnologia": None,
            "marca": None,
            "modelo": None,
            "mac": None,
            "so": None,
            "hostname": None,
            "ip": None,
            "marca_modelo_telemedicina": None,
            "mouse": None,
            "teclado": None,
            "anterior_asignado": row_dict.get("asignado_anterior"),
            "asignado_a": row_dict.get("asignado_actual"),
            "cargo": None,
            "area": None,
            "contacto": None,
            "fecha_asignacion": None,
            "cargado_nit": row_dict.get("nit"),
            "enviado_nit": None,
            "fecha_enviado": None,
            "guia": row_dict.get("documentos_entrega"),
            "procesador": None,
            "arquitectura_ram": None,
            "cantidad_ram": None,
            "tipo_disco": None,
            "almacenamiento": None,
            "placa_monitor": None,
            "serial_monitor": None,
            "marca_monitor": None,
            "modelo_monitor": None,
            "estado": row_dict.get("estado_general"),
            "disponible": 'Si' if (row_dict.get("estado_general") or '').lower() == 'disponible' else 'No',
            "observaciones": row_dict.get("observaciones"),
            "serial_telemedicina": None,
            "tipo_componente_adicional": None,
            "marca_modelo_componente_adicional": None,
            "serial_componente_adicional": None,
            "marca_modelo_telefono": None,
            "serial_telefono": None,
            "imei_telefono": None,
            "marca_modelo_impresora": None,
            "ip_impresora": None,
            "serial_impresora": None,
            "pin_impresora": None,
            "marca_modelo_cctv": None,
            "serial_cctv": None,
            "entrada_oc_compra": None,
            "fecha_llegada": None,
            "oc": None,
            "proveedor": None,
            "mueble_asignado": None,
            "descripcion_general": row_dict.get("descripcion_general"),
            "creador_registro": row_dict.get("creador_registro"),
            "fecha_creacion": row_dict.get("fecha_creacion"),
            "trazabilidad": row_dict.get("trazabilidad_soporte"),
            "documentos_entrega": row_dict.get("documentos_entrega"),
            "ciudad": None,
        }
        results.append(item)

    for row in individuales:
        row_dict = dict(row)
        item = map_individual_row(row_dict)
        item["tipo"] = "individual"
        results.append(item)

    # Agregar equipos del importador universal
    for row in inventario_items:
        row_dict = dict(row)
        item = {
            "tipo": "importado",
            "id": row_dict.get("id"),
            "serial": row_dict.get("serial"),
            "codigo_unificado": None,
            "codigo_individual": None,
            "placa": None,
            "anterior_placa": None,
            "sede": row_dict.get("sede_nombre") or "Sin sede",
            "ip_sede": None,
            "tecnologia": row_dict.get("tecnologia"),
            "marca": row_dict.get("marca"),
            "modelo": row_dict.get("modelo"),
            "mac": None,
            "so": None,
            "hostname": None,
            "ip": None,
            "marca_modelo_telemedicina": None,
            "mouse": row_dict.get("mouse"),
            "teclado": row_dict.get("teclado"),
            "anterior_asignado": None,
            "asignado_a": row_dict.get("asignado_a"),
            "cargo": None,
            "area": None,
            "contacto": None,
            "fecha_asignacion": None,
            "cargado_nit": None,
            "enviado_nit": None,
            "fecha_enviado": None,
            "guia": None,
            "procesador": row_dict.get("procesador"),
            "arquitectura_ram": None,
            "cantidad_ram": row_dict.get("ram"),
            "tipo_disco": row_dict.get("edisk"),
            "almacenamiento": None,
            "placa_monitor": None,
            "serial_monitor": None,
            "marca_monitor": None,
            "modelo_monitor": None,
            "estado": row_dict.get("estado"),
            "disponible": 'Si' if (row_dict.get("estado") or '').lower() in ['activo', 'disponible'] else 'No',
            "observaciones": row_dict.get("observaciones"),
            "serial_telemedicina": None,
            "tipo_componente_adicional": None,
            "marca_modelo_componente_adicional": None,
            "serial_componente_adicional": None,
            "marca_modelo_telefono": None,
            "serial_telefono": None,
            "imei_telefono": None,
            "marca_modelo_impresora": None,
            "ip_impresora": None,
            "serial_impresora": None,
            "pin_impresora": None,
            "marca_modelo_cctv": None,
            "serial_cctv": None,
            "entrada_oc_compra": None,
            "fecha_llegada": None,
            "oc": None,
            "proveedor": None,
            "mueble_asignado": None,
            "descripcion_general": None,
            "creador_registro": None,
            "fecha_creacion": row_dict.get("fecha_creacion"),
            "trazabilidad": None,
            "documentos_entrega": None,
            "ciudad": None,
        }
        results.append(item)

    return jsonify(results)

@inventarios_bp.route('/inventario/new', methods=['GET', 'POST'])
def new_inventario():
    if request.method == 'POST':
        data = build_individual_payload(request.form)
        insert_individual_record(data)
        flash('Equipo agregado exitosamente al inventario general.', 'success')
        return redirect(url_for('inventarios.inventarios'))

    sedes = get_sedes_options()
    return render_template(
        'new_inventario_individual.html',
        tecnologias=TECHNOLOGY_OPTIONS,
        sedes=sedes,
        technology_groups=TECHNOLOGY_FIELD_GROUPS,
        base_field_groups=BASE_FIELD_GROUPS
    )

@inventarios_bp.route('/inventario/agrupado/new', methods=['GET', 'POST'])
def new_inventario_agrupado():
    if request.method == 'POST':
        # Get all form fields for grouped inventory
        codigo_barras_unificado = request.form.get('codigo_barras_unificado')
        nit = request.form.get('nit')
        sede_id = request.form.get('sede_id')
        asignado_anterior = request.form.get('asignado_anterior')
        asignado_actual = request.form.get('asignado_actual')
        descripcion_general = request.form.get('descripcion_general')
        estado_general = request.form.get('estado_general')
        creador_registro = request.form.get('creador_registro')
        trazabilidad_soporte = request.form.get('trazabilidad_soporte')
        documentos_entrega = request.form.get('documentos_entrega')
        observaciones = request.form.get('observaciones')

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Generar código si no se proveyó
        if not codigo_barras_unificado:
            try:
                codigo_barras_unificado = generar_codigo_agrupado(conn, sede_id)
            except Exception:
                pass

        c.execute('''
            INSERT INTO equipos_agrupados (
                codigo_barras_unificado, nit, sede_id, asignado_anterior, asignado_actual,
                descripcion_general, estado_general, creador_registro, fecha_creacion,
                trazabilidad_soporte, documentos_entrega, observaciones, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?, datetime('now'), datetime('now'))
        ''', (
            codigo_barras_unificado, nit, sede_id, asignado_anterior, asignado_actual,
            descripcion_general, estado_general, creador_registro, trazabilidad_soporte,
            documentos_entrega, observaciones
        ))
        conn.commit()
        conn.close()

        flash('Equipo agrupado agregado exitosamente.', 'success')
        return redirect(url_for('inventarios.inventarios'))

    return render_template('new_inventario_agrupado.html')

@inventarios_bp.route('/inventario/individual/new', methods=['GET', 'POST'])
def new_inventario_individual():
    """
    Formulario dinámico para crear un nuevo equipo individual.
    """
    conn = get_connection()
    # Obtener dinámicamente los tipos de tecnología existentes para el selector
    tecnologias = conn.execute("SELECT DISTINCT tecnologia FROM equipos_individuales WHERE tecnologia IS NOT NULL ORDER BY tecnologia").fetchall()
    sedes = get_sedes_options()
    empleados = conn.execute("SELECT id, (nombre || ' ' || apellido) AS nombre_completo FROM empleados WHERE estado = 'activo' ORDER BY nombre, apellido").fetchall()
    conn.close()

    if request.method == 'POST':
        try:
            conn = get_connection()
            # Recolectar todos los campos posibles del formulario dinámico
            fields = {key: request.form.get(key) for key in INDIVIDUAL_DB_COLUMNS if request.form.get(key)}

            if not fields.get('tecnologia'):
                flash('El campo "Tipo de equipo / Tecnología" es obligatorio.', 'danger')
                return redirect(request.url)

            # Generar código de barras si no se proveyó
            if not fields.get('codigo_barras_individual'):
                fields['codigo_barras_individual'] = generar_codigo_individual(conn, fields.get('sede_id'), fields.get('tecnologia'))

            # Construir la consulta de inserción dinámicamente
            columns = ', '.join(fields.keys())
            placeholders = ', '.join('?' for _ in fields)
            values = tuple(fields.values())

            conn.execute(f"INSERT INTO equipos_individuales ({columns}) VALUES ({placeholders})", values)
            conn.commit()
            flash('Equipo individual creado exitosamente.', 'success')
            return redirect(url_for('inventarios.inventarios'))

        except sqlite3.IntegrityError as e:
            flash(f'Error de integridad: El serial o código de barras ya podría existir. ({e})', 'danger')
        except Exception as e:
            flash(f'Ocurrió un error inesperado: {e}', 'danger')
        finally:
            if conn:
                conn.close()

    return render_template(
        'new_inventario_individual.html',
        tecnologias=TECHNOLOGY_OPTIONS,
        sedes=sedes,
        empleados=empleados,
        technology_groups=TECHNOLOGY_FIELD_GROUPS,
        base_field_groups=BASE_FIELD_GROUPS
    )


@inventarios_bp.route('/inventarios/api/individuales_full', methods=['GET'])
def api_individuales_full():
    """Devuelve equipos individuales con todos los campos y filtros opcionales."""
    search_query = request.args.get('q_individual', '').strip()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    column_list = ", ".join(["ei.id"] + [f"ei.{col}" for col in INDIVIDUAL_DB_COLUMNS])
    query = f"""
        SELECT ei.*, 
               s.nombre as sede_nombre,
               s.ciudad as sede_ciudad,
               emp.nombre as empleado_nombre,
               emp.apellido as empleado_apellido
          FROM equipos_individuales ei
          LEFT JOIN sedes s ON s.id = ei.sede_id
          LEFT JOIN empleados emp ON (LOWER(emp.correo_office) = LOWER(ei.asignado_nuevo) OR LOWER(emp.nombre_completo) = LOWER(ei.asignado_nuevo))
         WHERE 1=1
    """
    params = []

    if search_query:
        like_query = f"%{search_query}%"
        query += """
            AND (
                ei.id LIKE ? OR
                ei.serial LIKE ? OR
                ei.codigo_barras_individual LIKE ? OR
                ei.placa LIKE ? OR
                ei.asignado_nuevo LIKE ? OR
                emp.cedula LIKE ? OR
                s.nombre LIKE ?
            )
        """
        params.extend([like_query] * 7)

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()

    result = []
    for row in rows:
        row_dict = dict(row)
        mapped = map_individual_row(row_dict)
        mapped["sede"] = row_dict.get("sede_nombre") or mapped.get("sede")
        result.append(mapped)

    return jsonify(result)


@inventarios_bp.route('/inventarios/api/delete_bulk', methods=['POST'])
def api_delete_bulk():
    """Elimina varios equipos (individual o agrupado)."""
    data = request.get_json(force=True)
    ids = data.get("ids") or []
    tipo = data.get("tipo")

    if not ids or tipo not in ["individual", "grouped"]:
        return jsonify({"error": "Faltan parametros"}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        if tipo == "individual":
            c.executemany("DELETE FROM equipos_individuales WHERE id = ?", [(i,) for i in ids])
            c.executemany("DELETE FROM hoja_vida_equipos WHERE equipo_id = ? AND tipo_equipo = 'individual'", [(i,) for i in ids])
        else:
            c.executemany("DELETE FROM equipos_componentes WHERE equipo_agrupado_id = ?", [(i,) for i in ids])
            c.executemany("DELETE FROM equipos_agrupados WHERE id = ?", [(i,) for i in ids])
            c.executemany("DELETE FROM hoja_vida_equipos WHERE equipo_id = ? AND tipo_equipo = 'agrupado'", [(i,) for i in ids])
        conn.commit()
        return jsonify({"message": "Equipos eliminados"}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@inventarios_bp.route('/inventario/edit/<tipo>/<int:inventario_id>', methods=['GET', 'POST'])
def edit_inventario(tipo, inventario_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if request.method == 'POST':
        if tipo == 'agrupado':
            # Get form data for grouped inventory
            codigo_barras_unificado = request.form.get('codigo_barras_unificado')
            nit = request.form.get('nit')
            sede_id = request.form.get('sede_id')
            asignado_anterior = request.form.get('asignado_anterior')
            asignado_actual = request.form.get('asignado_actual')
            descripcion_general = request.form.get('descripcion_general')
            estado_general = request.form.get('estado_general')
            creador_registro = request.form.get('creador_registro')
            trazabilidad_soporte = request.form.get('trazabilidad_soporte')
            documentos_entrega = request.form.get('documentos_entrega')
            observaciones = request.form.get('observaciones')

            # Update the grouped equipment
            c.execute('''
                UPDATE equipos_agrupados SET
                    codigo_barras_unificado = ?, nit = ?, sede_id = ?, asignado_anterior = ?, asignado_actual = ?,
                    descripcion_general = ?, estado_general = ?, creador_registro = ?, trazabilidad_soporte = ?,
                    documentos_entrega = ?, observaciones = ?, updated_at = datetime('now')
                WHERE id = ?
            ''', (codigo_barras_unificado, nit, sede_id, asignado_anterior, asignado_actual,
                  descripcion_general, estado_general, creador_registro, trazabilidad_soporte,
                  documentos_entrega, observaciones, inventario_id))

            flash('Equipo agrupado actualizado exitosamente.', 'success')

        elif tipo == 'individual':
            data = build_individual_payload(request.form)
            set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
            values = list(data.values())
            values.append(inventario_id)

            c.execute(
                f"""
                UPDATE equipos_individuales
                   SET {set_clause},
                       updated_at = datetime('now')
                 WHERE id = ?
                """,
                values
            )

            flash('Equipo individual actualizado exitosamente.', 'success')

        conn.commit()
        conn.close()
        return redirect(url_for('inventarios.inventarios'))

    else:
        if tipo == 'agrupado':
            # Get the grouped equipment data
            c.execute("SELECT * FROM equipos_agrupados WHERE id = ?", (inventario_id,))
            inventario = c.fetchone()
            template = 'edit_inventario_agrupado.html'
        elif tipo == 'individual':
            # Get the individual equipment data
            c.execute("SELECT * FROM equipos_individuales WHERE id = ?", (inventario_id,))
            inventario = c.fetchone()
            template = 'edit_inventario.html'
        else:
            conn.close()
            flash('Tipo de equipo inválido.', 'danger')
            return redirect(url_for('inventarios.inventarios'))

        conn.close()

        if not inventario:
            flash('Equipo no encontrado.', 'danger')
            return redirect(url_for('inventarios.inventarios'))

        return render_template(template, inventario=inventario)

@inventarios_bp.route('/inventario/delete/<int:inventario_id>', methods=['POST'])
def delete_inventario(inventario_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Check if the equipment exists
    c.execute("SELECT * FROM equipos_agrupados WHERE id = ?", (inventario_id,))
    inventario = c.fetchone()

    if not inventario:
        conn.close()
        flash('Equipo agrupado no encontrado.', 'danger')
        return redirect(url_for('inventarios.inventarios'))

    # Delete the grouped equipment
    c.execute("DELETE FROM equipos_agrupados WHERE id = ?", (inventario_id,))
    conn.commit()
    conn.close()

    flash('Equipo agrupado eliminado exitosamente.', 'success')
    return redirect(url_for('inventarios.inventarios'))

@inventarios_bp.route('/inventarios/<int:id>/components')
def inventario_components(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get grouped equipment details
    c.execute("SELECT * FROM equipos_agrupados WHERE id = ?", (id,))
    equipo_agrupado = c.fetchone()

    if not equipo_agrupado:
        conn.close()
        flash('Equipo agrupado no encontrado.', 'danger')
        return redirect(url_for('inventarios.inventarios'))

    # Get components of the grouped equipment
    c.execute("SELECT * FROM equipos_componentes WHERE equipo_agrupado_id = ?", (id,))
    componentes = c.fetchall()

    conn.close()
    return render_template('inventario_components.html', equipo_agrupado=equipo_agrupado, componentes=componentes)

@inventarios_bp.route('/inventarios/individual/<int:id>')
def inventario_individual_detail(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get individual equipment details
    c.execute("SELECT * FROM equipos_individuales WHERE id = ?", (id,))
    equipo_individual = c.fetchone()

    if not equipo_individual:
        conn.close()
        flash('Equipo individual no encontrado.', 'danger')
        return redirect(url_for('inventarios.inventarios'))

    conn.close()
    return render_template('assign_inventario.html', equipo_individual=equipo_individual)

@inventarios_bp.route('/inventarios/api/search/<query>')
def api_search_inventory(query):
    """
    Búsqueda general para el tab "Inventario General".

    - Si query == "_all_" trae todo.
    - Permite filtros opcionales por tecnología y estado vía query string:
        ?tecnologia=CPU&estado=asignado
    - Devuelve tanto equipos agrupados como individuales.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    tecnologia = request.args.get('tecnologia', '').strip()
    estado = request.args.get('estado', '').strip().lower()

    like_query = '%' if query == '_all_' else f'%{query}%'

    # Buscar en equipos agrupados (mantener compatibilidad con tu diseño)
    c.execute("""
        SELECT 'agrupado' as tipo, id, codigo_barras_unificado as codigo, '' as serial,
               '' as marca, '' as modelo, asignado_actual as asignado,
               CASE
                   WHEN sede_id = 1 THEN 'Sede Principal Bogotá'
                   WHEN sede_id = 2 THEN 'Sede Norte Bogotá'
                   WHEN sede_id = 3 THEN 'Sede Sur Bogotá'
                   WHEN sede_id = 4 THEN 'Medellín'
                   WHEN sede_id = 5 THEN 'Sede Cali'
                   WHEN sede_id = 6 THEN 'Sede Barranquilla'
                   WHEN sede_id = 7 THEN 'Sede Cartagena'
                   WHEN sede_id = 8 THEN 'Sede Bucaramanga'
                   WHEN sede_id = 9 THEN 'Sede Pereira'
                   WHEN sede_id = 10 THEN 'Sede Manizales'
                   WHEN sede_id = 11 THEN 'Sede Ibagué'
                   WHEN sede_id = 12 THEN 'Sede Villavicencio'
                   WHEN sede_id = 13 THEN 'Sede Neiva'
                   ELSE 'No asignada'
               END as sede,
               estado_general as estado,
               '' as tecnologia
        FROM equipos_agrupados
        WHERE (codigo_barras_unificado LIKE ? OR descripcion_general LIKE ?)
    """, (like_query, like_query))
    agrupados = c.fetchall()

    # Buscar en equipos individuales (Inventario General maestro)
    sql_ind = """
        SELECT 'individual' as tipo, id, codigo_barras_individual as codigo, serial,
               marca, modelo, asignado_nuevo as asignado,
               CASE
                   WHEN sede_id = 1 THEN 'Sede Principal Bogotá'
                   WHEN sede_id = 2 THEN 'Sede Norte Bogotá'
                   WHEN sede_id = 3 THEN 'Sede Sur Bogotá'
                   WHEN sede_id = 4 THEN 'Medellín'
                   WHEN sede_id = 5 THEN 'Sede Cali'
                   WHEN sede_id = 6 THEN 'Sede Barranquilla'
                   WHEN sede_id = 7 THEN 'Sede Cartagena'
                   WHEN sede_id = 8 THEN 'Sede Bucaramanga'
                   WHEN sede_id = 9 THEN 'Sede Pereira'
                   WHEN sede_id = 10 THEN 'Sede Manizales'
                   WHEN sede_id = 11 THEN 'Sede Ibagué'
                   WHEN sede_id = 12 THEN 'Sede Villavicencio'
                   WHEN sede_id = 13 THEN 'Sede Neiva'
                   ELSE 'No asignada'
               END as sede,
               COALESCE(LOWER(estado), '') as estado,
               COALESCE(UPPER(tecnologia), '') as tecnologia
        FROM equipos_individuales
        WHERE (
            codigo_barras_individual LIKE ?
            OR serial LIKE ?
            OR marca LIKE ?
            OR modelo LIKE ?
        )
    """
    params = [like_query, like_query, like_query, like_query]

    if tecnologia:
        sql_ind += " AND UPPER(tecnologia) = ?"
        params.append(tecnologia.upper())

    if estado:
        sql_ind += " AND LOWER(estado) = ?"
        params.append(estado)

    c.execute(sql_ind, params)
    individuales = c.fetchall()
    conn.close()

    results = []

    for row in agrupados:
        results.append({
            "tipo": row[0],
            "id": row[1],
            "codigo": row[2],
            "serial": row[3],
            "marca": row[4],
            "modelo": row[5],
            "asignado": row[6],
            "sede": row[7],
            "estado": row[8],
            "tecnologia": row[9],
        })

    for row in individuales:
        results.append({
            "tipo": row[0],
            "id": row[1],
            "codigo": row[2],
            "serial": row[3],
            "marca": row[4],
            "modelo": row[5],
            "asignado": row[6],
            "sede": row[7],
            "estado": row[8],
            "tecnologia": row[9],
        })

    return jsonify(results)

@inventarios_bp.route('/inventarios/api/search_grouped', methods=['POST'])
def api_search_grouped():
    data = request.get_json()

    serial = data.get('serial', '')
    codigo = data.get('codigo', '')
    user = data.get('user', '')
    id_param = data.get('id', '')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    query = "SELECT * FROM equipos_agrupados WHERE 1=1"
    params = []

    if serial:
        query += " AND (codigo_barras_unificado LIKE ? OR descripcion_general LIKE ?)"
        params.extend([f"%{serial}%", f"%{serial}%"])

    if codigo:
        query += " AND codigo_barras_unificado LIKE ?"
        params.append(f"%{codigo}%")

    if user:
        query += " AND asignado_actual LIKE ?"
        params.append(f"%{user}%")

    if id_param:
        query += " AND id = ?"
        params.append(id_param)

    c.execute(query, params)
    results = c.fetchall()
    conn.close()

    # Convert results to a JSON-serializable format
    serialized_results = [
        {
            'id': row[0],
            'codigo_barras_unificado': row[1],
            'nit': row[2],
            'sede_id': row[3],
            'asignado_anterior': row[4],
            'asignado_actual': row[5],
            'descripcion_general': row[6],
            'estado_general': row[7],
            'creador_registro': row[8],
            'fecha_creacion': row[9],
            'trazabilidad_soporte': row[10],
            'documentos_entrega': row[11],
            'observaciones': row[12],
            'created_at': row[13],
            'updated_at': row[14]
        }
        for row in results
    ]

    return jsonify(serialized_results)


@inventarios_bp.route('/inventarios/api/asignados', methods=['GET'])
def api_get_asignados():
    """Devuelve equipos (individuales y agrupados) que tienen asignaciA3n para alimentar la pestaA�a Asignados."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    resultados = []

    # Equipos individuales asignados
    c.execute("""
        SELECT * FROM equipos_individuales
        WHERE (asignado_nuevo IS NOT NULL AND TRIM(asignado_nuevo) != '')
           OR LOWER(COALESCE(estado,'')) IN ('asignado','activo','usado','en uso')
    """)
    for row in c.fetchall():
        mapped = map_individual_row(dict(row))
        resultados.append({
            "id": mapped["id"],
            "codigo": mapped["codigo_individual"] or mapped["placa"],
            "marca": mapped["marca"],
            "modelo": mapped["modelo"],
            "serial": mapped["serial"],
            "usuario_asignado": mapped["asignado_a"] or "",
            "sede": mapped["sede"],
            "fecha_asignacion": mapped["fecha_asignacion"],
            "estado": mapped["estado"] or "asignado",
            "tipo": "individual",
        })

    # Equipos agrupados asignados
    c.execute("""
        SELECT id, codigo_barras_unificado, asignado_actual, sede_id, estado_general,
               fecha_creacion, descripcion_general
        FROM equipos_agrupados
        WHERE (asignado_actual IS NOT NULL AND TRIM(asignado_actual) != '')
           OR LOWER(COALESCE(estado_general,'')) IN ('asignado','activo','usado','en uso')
    """)
    for row in c.fetchall():
        resultados.append({
            "id": row["id"],
            "codigo": row["codigo_barras_unificado"],
            "marca": row["descripcion_general"] or "",
            "modelo": "",
            "serial": "",
            "usuario_asignado": row["asignado_actual"] or "",
            "sede": get_sede_name(row["sede_id"]),
            "fecha_asignacion": row["fecha_creacion"],
            "estado": row["estado_general"] or "asignado",
            "tipo": "agrupado",
        })

    conn.close()
    return jsonify(resultados)


@inventarios_bp.route('/inventarios/api/assign_equipment', methods=['POST'])
def api_assign_equipment():
    """
    Asigna equipo a usuario y sede específica.
    Recibe: equipo_id, tipo_equipo, user_id, sede_id
    """
    data = request.get_json()
    equipo_id = data.get('equipo_id')
    tipo_equipo = data.get('tipo_equipo')  # 'agrupado' o 'individual'
    user_id = data.get('user_id')
    sede_id = data.get('sede_id')

    if not all([equipo_id, tipo_equipo, user_id, sede_id]):
        return jsonify({"error": "Todos los campos son requeridos"}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    try:
        # Obtener info del usuario
        c.execute("SELECT nombre, apellido, cedula FROM empleados WHERE id = ?", (user_id,))
        user = c.fetchone()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        user_name = f"{user[0]} {user[1]}"
        user_doc = user[2]

        # Actualizar asignación según tipo de equipo
        if tipo_equipo == 'agrupado':
            c.execute("""
                UPDATE equipos_agrupados
                SET asignado_actual = ?, sede_id = ?, estado_general = 'asignado', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user_name, sede_id, equipo_id))
        elif tipo_equipo == 'individual':
            c.execute("""
                UPDATE equipos_individuales
                SET asignado_nuevo = ?, sede_id = ?, estado = 'asignado', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user_name, sede_id, equipo_id))
        else:
            return jsonify({"error": "Tipo de equipo inválido"}), 400

        # Registrar en hoja de vida
        c.execute("""
            INSERT INTO hoja_vida_equipos (
                equipo_id, tipo_equipo, accion, usuario_anterior, usuario_nuevo,
                sede_anterior, sede_nueva, fecha_accion, observaciones
            ) VALUES (?, ?, 'asignacion', NULL, ?, NULL, ?, date('now'), 'Asignación automática desde sistema')
        """, (equipo_id, tipo_equipo, user_name, sede_id))

        conn.commit()
        return jsonify({
            "message": f"Equipo asignado exitosamente a {user_name}",
            "user_name": user_name,
            "sede_id": sede_id
        })

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@inventarios_bp.route('/inventarios/api/technology/<tech>', methods=['GET'])
def api_inventory_by_technology(tech):
    """Lista equipos individuales filtrados por tecnologia (uso en pestaña Tipo de Tecnologia)."""
    if not tech:
        return jsonify([])

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT *
        FROM equipos_individuales
        WHERE UPPER(COALESCE(tecnologia,'')) = UPPER(?)
        ORDER BY id DESC
    """, (tech,))
    rows = c.fetchall()
    conn.close()
    return jsonify([map_individual_row(dict(r)) for r in rows])


@inventarios_bp.route('/inventarios/api/search_users/<query>', methods=['GET'])
def api_search_users_inventory(query):
    """
    API para buscar usuarios para asignación de equipos.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute("""
            SELECT id, nombre, apellido, cedula, correo_office, cargo, departamento, sede_id
            FROM empleados
            WHERE LOWER(nombre) LIKE LOWER(?)
               OR LOWER(apellido) LIKE LOWER(?)
               OR cedula LIKE ?
               OR LOWER(correo_office) LIKE LOWER(?)
            LIMIT 20
        """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"))
        users = c.fetchall()
        result = []
        for user in users:
            result.append({
                "id": user["id"],
                "name": f"{user['nombre']} {user['apellido']}",
                "document": user["cedula"],
                "email": user["correo_office"],
                "position": user["cargo"],
                "department": user["departamento"],
                "sede_id": user["sede_id"]
            })
    finally:
        conn.close()
    return jsonify(result)


@inventarios_bp.route('/inventarios/api/life_sheet/<tipo>/<int:equipo_id>', methods=['GET'])
def api_life_sheet(tipo, equipo_id):
    """
    Obtiene la hoja de vida de un equipo.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        c.execute("""
            SELECT * FROM hoja_vida_equipos
            WHERE equipo_id = ? AND tipo_equipo = ?
            ORDER BY fecha_accion DESC
        """, (equipo_id, tipo))
        records = c.fetchall()
        result = [dict(row) for row in records]
    finally:
        conn.close()
    return jsonify(result)

@inventarios_bp.route('/inventarios/api/decommission/<tipo>/<int:equipo_id>', methods=['POST'])
def api_decommission_equipment(tipo, equipo_id):
    """
    Da de baja un equipo (cambia estado a 'baja').
    """
    data = request.get_json()
    reason = data.get('reason', 'Dado de baja por usuario')

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        if tipo == 'grouped':
            c.execute("""
                UPDATE equipos_agrupados
                SET estado_general = 'baja', observaciones = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (reason, equipo_id))
        elif tipo == 'individual':
            c.execute("""
                UPDATE equipos_individuales
                SET estado = 'baja', observaciones = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (reason, equipo_id))

        # Registrar en hoja de vida
        c.execute("""
            INSERT INTO hoja_vida_equipos (
                equipo_id, tipo_equipo, accion, usuario_anterior, usuario_nuevo,
                sede_anterior, sede_nueva, fecha_accion, observaciones
            ) VALUES (?, ?, 'baja', NULL, NULL, NULL, NULL, date('now'), ?)
        """, (equipo_id, tipo, reason))

        conn.commit()
        return jsonify({"message": "Equipo dado de baja exitosamente"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@inventarios_bp.route('/inventarios/api/reassign_equipment', methods=['POST'])
def api_reassign_equipment():
    """
    Reasigna un equipo a un nuevo usuario.
    """
    data = request.get_json()
    equipo_id = data.get('equipo_id')
    tipo_equipo = data.get('tipo_equipo')
    user_id = data.get('user_id')
    assignment_date = data.get('assignment_date')
    notes = data.get('notes', '')

    if not all([equipo_id, tipo_equipo, user_id, assignment_date]):
        return jsonify({"error": "Todos los campos son requeridos"}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        # Obtener info del usuario
        c.execute("SELECT nombre, apellido, cedula FROM empleados WHERE id = ?", (user_id,))
        user = c.fetchone()
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        user_name = f"{user[0]} {user[1]}"

        # Actualizar asignación
        if tipo_equipo == 'agrupado':
            c.execute("""
                UPDATE equipos_agrupados
                SET asignado_actual = ?, estado_general = 'asignado', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user_name, equipo_id))
        elif tipo_equipo == 'individual':
            c.execute("""
                UPDATE equipos_individuales
                SET asignado_nuevo = ?, estado = 'asignado', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user_name, equipo_id))
        else:
            return jsonify({"error": "Tipo de equipo inválido"}), 400

        # Registrar en hoja de vida
        c.execute("""
            INSERT INTO hoja_vida_equipos (
                equipo_id, tipo_equipo, accion, usuario_anterior, usuario_nuevo,
                sede_anterior, sede_nueva, fecha_accion, observaciones
            ) VALUES (?, ?, 'reasignacion', NULL, ?, NULL, NULL, ?, ?)
        """, (equipo_id, tipo_equipo, user_name, assignment_date, notes))

        conn.commit()
        return jsonify({"message": f"Equipo reasignado exitosamente a {user_name}"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@inventarios_bp.route('/inventarios/api/delete/<tipo>/<int:equipo_id>', methods=['DELETE'])
def api_delete_equipment(tipo, equipo_id):
    """
    Elimina un equipo de la base de datos.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        if tipo == 'individual':
            # Eliminar de equipos_individuales
            c.execute("DELETE FROM equipos_individuales WHERE id = ?", (equipo_id,))
        elif tipo == 'grouped':
            # Eliminar componentes primero, luego el equipo agrupado
            c.execute("DELETE FROM equipos_componentes WHERE equipo_agrupado_id = ?", (equipo_id,))
            c.execute("DELETE FROM equipos_agrupados WHERE id = ?", (equipo_id,))
        else:
            return jsonify({"error": "Tipo de equipo inválido"}), 400

        # Eliminar registros de hoja de vida
        c.execute("DELETE FROM hoja_vida_equipos WHERE equipo_id = ? AND tipo_equipo = ?", (equipo_id, tipo))

        conn.commit()
        return jsonify({"message": "Equipo eliminado exitosamente"})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@inventarios_bp.route('/inventarios/api/components/<int:equipo_id>', methods=['GET'])
def api_get_components(equipo_id):
    """
    Obtiene los componentes de un equipo agrupado (periféricos de equipos individuales asociados).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    try:
        # Get the codigo_unificado of the grouped equipment
        c.execute("SELECT codigo_barras_unificado FROM equipos_agrupados WHERE id = ?", (equipo_id,))
        grouped = c.fetchone()
        if not grouped:
            return jsonify([])

        codigo_unificado = grouped['codigo_barras_unificado']

        # Get individual equipment with the same codigo_unificado
        c.execute("SELECT * FROM equipos_individuales WHERE codigo_unificado = ?", (codigo_unificado,))
        individuals = c.fetchall()

        result = []
        for ind in individuals:
            ind_dict = dict(ind)
            mapped = map_individual_row(ind_dict)
            # Add peripherals as components
            if mapped['mouse']:
                result.append({
                    "tipo": "Mouse",
                    "marca_modelo": mapped['mouse'],
                    "serial": None
                })
            if mapped['teclado']:
                result.append({
                    "tipo": "Teclado",
                    "marca_modelo": mapped['teclado'],
                    "serial": None
                })
            if mapped['marca_modelo_telemedicina']:
                result.append({
                    "tipo": "Telemedicina",
                    "marca_modelo": mapped['marca_modelo_telemedicina'],
                    "serial": mapped['serial_telemedicina']
                })
            if mapped['marca_modelo_cctv']:
                result.append({
                    "tipo": "CCTV",
                    "marca_modelo": mapped['marca_modelo_cctv'],
                    "serial": mapped['serial_cctv']
                })
            if mapped['marca_modelo_impresora']:
                result.append({
                    "tipo": "Impresora",
                    "marca_modelo": mapped['marca_modelo_impresora'],
                    "serial": mapped['serial_impresora']
                })
            # Add more peripherals as needed
        return jsonify(result)
    finally:
        conn.close()
