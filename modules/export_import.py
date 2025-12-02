import os
import time
import json
import unicodedata
import sqlite3
import csv
import io
import re
import warnings
import pandas as pd
from flask import (
    Blueprint, render_template, request,
    flash, redirect, url_for, send_file
)

export_import_bp = Blueprint(
    "export_import",
    __name__,
    url_prefix="/importador"
)

DB_PATH = "workmanager_erp.db"
TMP_DIR = "tmp_imports"
os.makedirs(TMP_DIR, exist_ok=True)
TABLE_COL_CACHE = {}

# ==========================
# 🔠 NORMALIZACIÓN DE TEXTO
# ==========================

def normalize_text(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.strip().lower()
    # quitar acentos
    s = "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )
    # reemplazar separadores por espacio
    for ch in [",", ";", ":", "-", "_", ".", "/", "\\"]:
        s = s.replace(ch, " ")
    # colapsar espacios
    s = " ".join(s.split())
    return s

# ===========================================
# 🧠 SINÓNIMOS DE ENCABEZADOS (PSEUDO-IA)
# ===========================================

# Canonical -> lista de variantes que puede traer el archivo
HEADER_SYNONYMS = {
    # INVENTARIO TECNOLÓGICO / INDIVIDUAL
    "serial": [
        "serial", "no serial", "n serie", "serie", "serial equipo",
        "n° serie", "nro serial"
    ],
    "placa": [
        "placa", "activo fijo", "codigo activo", "codigo placa"
    ],
    "codigo_barras_individual": [
        "codigo barras", "codigo de barras", "codigo barras individual",
        "codigo individual", "codigo interno", "codigo", "cod barras"
    ],
    "modelo": ["modelo", "reference", "referencia"],
    "marca": ["marca", "fabricante"],
    "procesador": ["procesador", "cpu", "tipo procesador"],
    "arch_ram": ["tipo memoria ram", "tipo de ram", "arquitectura ram"],
    "cantidad_ram": [
        "cantidad ram", "ram", "memoria ram",
        "capacidad ram", "tamano ram"
    ],
    "so": [
        "so", "sistema operativo", "os", "windows", "linux"
    ],
    "fecha": [
        "fecha", "fecha asignacion", "fecha de asignacion"
    ],
    "fecha_llegada": [
        "fecha llegada", "fecha de llegada", "fecha recepcion"
    ],
    "tipo_disco": ["tipo disco", "tipo de disco"],
    "espacio_disco": [
        "espacio disco", "tamano disco", "capacidad disco",
        "disco gb", "tipo de disco gb"
    ],
    "hostname": ["hostname", "nombre equipo", "equipo", "host"],
    "estado": ["estado", "estado fisico", "estado equipo"],
    "tecnologia": ["tecnologia", "tipo dispositivo", "tipo de dispositivo"],
    "observaciones": ["observaciones", "comentarios", "nota", "novedad"],
    "asignado_nuevo": [
        "asignado", "asignado a", "usuario asignado",
        "usuario", "nombre usuario", "asignado nuevo"
    ],
    "ciudad": ["ciudad", "sede ciudad", "ubicacion"],
    "ip": ["ip", "direccion ip", "ip equipo"],
    "ip_sede": ["ip sede", "ip oficina", "ip sucursal"],
    "mac": ["mac", "direccion mac", "mac address"],
    "anterior_placa": ["anterior placa", "placa anterior"],
    "marca_monitor": ["marca monitor", "marca pantalla"],
    "modelo_monitor": ["modelo monitor", "modelo pantalla"],
    "serial_monitor": ["serial monitor", "serie monitor"],
    "placa_monitor": ["placa monitor", "activo monitor"],
    "proveedor": [
        "proveedor", "fabricante", "distribuidor"
    ],
    "oc": [
        "oc", "orden de compra", "orden compra"
    ],
    "mouse": ["mouse", "raton"],
    "teclado": ["teclado", "keyboard"],
    "marca_modelo_telemedicina": ["marca telemedicina", "modelo telemedicina"],
    "serial_telemedicina": ["serial telemedicina"],
    "cargado_nit": ["cargado nit", "nit cargado"],
    "enviado_nit": ["enviado nit", "nit enviado"],
    "fecha_enviado": ["fecha enviado", "fecha envio"],
    "guia": ["guia", "numero guia", "tracking"],
    "contacto": ["contacto", "telefono contacto", "persona contacto"],
    "tipo_componente_adicional": ["tipo componente", "tipo accesorio"],
    "marca_modelo_componente_adicional": [
        "marca componente", "modelo componente", "marca y modelo componente"
    ],
    "serial_componente_adicional": ["serial componente", "serie componente"],
    "marca_modelo_telefono": ["marca telefono", "modelo telefono", "marca y modelo telefono"],
    "serial_telefono": ["serial telefono", "serie telefono"],
    "imei_telefono": ["imei", "imei telefono"],
    "marca_modelo_impresora": [
        "marca impresora", "modelo impresora", "marca y modelo impresora"
    ],
    "ip_impresora": ["ip impresora", "direccion ip impresora"],
    "serial_impresora": ["serial impresora", "serie impresora"],
    "pin_impresora": ["pin impresora", "clave impresora"],
    "marca_modelo_cctv": ["marca cctv", "modelo cctv"],
    "serial_cctv": ["serial cctv", "serie cctv"],
    "mueble_asignado": ["mueble asignado", "ubicacion mueble", "puesto asignado"],
    "creador_registro": [
        "creador registro", "creado por", "registrado por"
    ],
    "disponible": [
        "disponible", "disponibilidad"
    ],

    # AGRUPADO
    "codigo_unificado": [
        "codigo unificado", "codigo agru", "codigo agrupado",
        "codigo paquete"
    ],

    # EMPLEADOS
    "cedula": [
        "cedula", "n documento", "documento", "numero documento",
        "cedula usuario"
    ],
    "nombre": ["nombre", "nombres"],
    "apellido": ["apellido", "apellidos"],
    "nombre_completo": ["nombres y apellidos", "nombre completo"],

    # LICENCIAS
    "email": ["email", "correo", "correo office", "correo electronico"],
    "tipo_licencia": ["licencia", "tipo licencia", "producto"],
    "usuario_lic": ["usuario licencia", "usuario office", "usuario cuenta"],
    # BAJAS
    "tipo_inventario": ["tipo inventario", "tecnologia", "tipo dispositivo"],
    "motivo_baja": ["motivo de baja", "motivo", "observaciones de baja"],
    "responsable_baja": ["responsable", "usuario"],
    "documentos_soporte": ["documentos", "documentos soporte"],
    "fotografias_soporte": ["fotografias", "fotos", "evidencias"],
    # INSUMOS / ACCESORIOS
    "nombre_insumo": ["nombre de la parte", "nombre insumo", "articulo"],
    "cantidad_total": ["cantidad", "cant"],
    "ubicacion": ["area", "ubicacion"],
    "asignado_a": ["asignado", "asignado a", "usuario"],
    "serial_equipo": ["placa", "serial"],
    # TANDAS NUEVAS
    "numero_tanda": ["numero tanda", "tanda", "tandas nuevas"],
    "descripcion": ["descripcion", "observacion"],
    "cantidad_equipos": ["cantidad equipos", "cantidad", "cant"],
    "proveedor": ["proveedor"],
    "valor_total": ["valor", "valor total"],
    # SEDES
    "codigo_sede": ["codigo sede", "codigo_sede", "cod sede", "cod_sede"],
    "nombre_sede": ["sede", "nombre sede", "nombre_sede", "sede nombre"],
    "departamento": ["departamento", "depto"],
    "direccion": ["direccion", "dirección", "direccion sede"],
    "responsable_sede": ["responsable", "responsable sede", "contacto sede"],
    "telefono_sede": ["telefono", "teléfono", "telefono sede", "telefono_sede"],
    "email_sede": ["email sede", "correo sede", "correo_sede"],
    # ADMINISTRATIVO (inventario_administrativo)
    "tipo_mueble": ["tipo mueble", "tipo_mueble", "mueble", "categoria mueble"],
    "sede_id": ["sede_id", "id sede", "id_sede"],
    "codigo_interno": ["codigo interno", "codigo_interno", "codigo item"],
    "descripcion_item": ["descripcion item", "descripcion_item", "descripcion mueble", "detalle"],
    "fecha_compra": ["fecha compra", "fecha_compra"],
    "asignado_a": ["asignado a", "asignado_a", "responsable"],
    "cantidad": ["cantidad", "cantidad total", "cant"],
    "area_recibe": ["area recibe", "area_recibe", "area asignada"],
    "cargo_recibe": ["cargo recibe", "cargo_recibe"],
    "creador_registro": ["creador", "creador_registro", "registrado por"],
}

# Extensiones adicionales de sinónimos (cabeceras observadas en cargas reales)
EXTRA_SYNONYMS = {
    "serial_o_mac": ["serial o mac", "serial mac", "serial_mac", "serial / mac"],
    "codigo_barras_individual": [
        "codigo unificado", "codigo unico hv equipo", "codigo interno equipo",
        "codigo activo", "codigo barras individual"
    ],
    "arch_ram": ["arqui ram", "arquitectura ram"],
    "cantidad_ram": ["arqui ram", "arquitectura ram", "cantidad de ram"],
    "espacio_disco": ["espacio de disco"],
    "tecnologia": ["tipo de tecnologia", "tipo tecnologia"],
    "observaciones": ["observacion"],
    "asignado_nuevo": ["asignado nuevo", "anterior asignado"],
    "ciudad": ["area o ciudad"],
    "ip_sede": ["ip red"],
    "marca_monitor": ["marca de monitor"],
    "modelo_monitor": ["modelo de monitor"],
    "entrada_oc_compra": ["entrada oc compra", "entrada oc", "oc compra", "oc"],
    "fecha_llegada": ["fecha de llegada", "fecha enviado", "fecha envio", "fecha cambio"],
    "enviado_cargado": ["enviado /cargado", "enviado cargado"],
    "formato": ["formato"],
    "total_equipos": ["equipos disponibles", "equipos asignados", "total equipos"],
    "codigo_interno": ["codigo interno equipo", "codigo interno item", "codigo interno"],
    "responsable": ["responsable sede", "responsable_baja"],
}

for k, v in EXTRA_SYNONYMS.items():
    if k in HEADER_SYNONYMS:
        HEADER_SYNONYMS[k].extend(v)
    else:
        HEADER_SYNONYMS[k] = v

# Construimos un mapa "encabezado normalizado" -> "campo canonico"
HEADER_MAP = {}
for canonical, variants in HEADER_SYNONYMS.items():
    for v in variants:
        HEADER_MAP[normalize_text(v)] = canonical


# ==========================
# 🔌 HELPERS DB
# ==========================

def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _get_table_columns(cur, table_name):
    """Devuelve set de columnas reales de la tabla (caché en memoria)."""
    if table_name in TABLE_COL_CACHE:
        return TABLE_COL_CACHE[table_name]
    cur.execute(f"PRAGMA table_info({table_name})")
    cols = {row[1] for row in cur.fetchall()}  # segundo campo es nombre columna
    TABLE_COL_CACHE[table_name] = cols
    return cols


# ==========================
# 🎯 DETECCIÓN DE DESTINO
# ==========================

def detect_target_from_headers(norm_headers):
    """Intenta adivinar a qué módulo pertenece el archivo."""
    headers_set = set(norm_headers)

    if {"email", "tipo_licencia"} & {
        HEADER_MAP.get(h) for h in headers_set
    }:
        return "licencias"

    if {"cedula", "nombre"} & {
        HEADER_MAP.get(h) for h in headers_set
    }:
        return "empleados"

    if {"serial", "codigo_barras_individual"} & {
        HEADER_MAP.get(h) for h in headers_set
    }:
        return "inventario"

    if {"motivo_baja"} & {HEADER_MAP.get(h) for h in headers_set}:
        return "bajas"

    if {"nombre_insumo", "cantidad_total"} & {HEADER_MAP.get(h) for h in headers_set}:
        return "insumos"

    if {"numero_tanda", "cantidad_equipos"} & {HEADER_MAP.get(h) for h in headers_set}:
        return "tandas"

    if {"codigo_sede", "nombre_sede"} & {HEADER_MAP.get(h) for h in headers_set}:
        return "sedes"

    if {"tipo_mueble", "codigo_interno"} & {HEADER_MAP.get(h) for h in headers_set}:
        return "inventario_administrativo"

    return "inventario"  # default


# ==================================
# 🧠 MAPEADOR UNIVERSAL DE COLUMNAS
# ==================================

def build_column_mapping(headers):
    """
    Recibe lista de encabezados originales
    Devuelve dict: {original: canonical o None}
    """
    mapping = {}
    norm_headers = []

    for orig in headers:
        norm = normalize_text(orig)
        # Si viene deduplicado (ej: "serial_2"), probar sin sufijo numérico
        norm_base = re.sub(r"_(\d+)$", "", norm)
        norm_headers.append(norm_base)
        canonical = HEADER_MAP.get(norm) or HEADER_MAP.get(norm_base)
        mapping[orig] = canonical  # puede ser None
    return mapping, norm_headers


# ==============================
# 📥 LECTURA DE ARCHIVOS
# ==============================

def _find_header_row(df):
    """Detecta la fila que parece encabezado en hojas desorganizadas."""
    max_check = min(len(df), 25)
    best_idx = 0
    best_score = 0
    for idx in range(0, max_check):
        row = df.iloc[idx]
        non_null = row.dropna()
        if len(non_null) < 3:
            continue
        text_like = 0
        for val in non_null:
            s = str(val).strip()
            if s and not s.isdigit() and len(s) <= 64:
                text_like += 1
        if text_like > best_score:
            best_score = text_like
            best_idx = idx
    return best_idx

def _normalize_dataframe(df):
    """Usa la fila detectada como encabezado y devuelve DataFrame limpio."""
    header_idx = _find_header_row(df)
    headers = []
    for val in df.iloc[header_idx]:
        headers.append(str(val).strip() if pd.notna(val) else "")
    clean = df.iloc[header_idx + 1:].copy()
    clean.columns = headers
    # Eliminar columnas vacías
    clean = clean[[c for c in clean.columns if c]]
    # Eliminar filas totalmente vacías
    clean = clean.dropna(how="all")
    return clean

def _reset_stream(stream):
    """Rebobina flujos si soportan seek para reutilizarlos en relecturas."""
    if hasattr(stream, "seek"):
        try:
            stream.seek(0)
        except Exception:
            pass

def _read_csv_loose(file_path_or_obj):
    """
    Lector de CSV tolerante: no omite filas, rellena/podA3 columnas para alinear longitudes.
    """
    # Preparar flujo de lectura
    if hasattr(file_path_or_obj, "read"):
        content = file_path_or_obj.read()
        _reset_stream(file_path_or_obj)
        if not isinstance(content, str):
            content = content.decode("latin1", errors="ignore")
        data_stream = io.StringIO(content)
    else:
        data_stream = open(file_path_or_obj, "r", encoding="latin1", newline="")

    with data_stream as f:
        sample = f.read(2048)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;|\t")
        except Exception:
            dialect = csv.excel
        f.seek(0)
        reader = csv.reader(f, dialect)
        rows = [row for row in reader]

    if not rows:
        return pd.DataFrame()

    max_cols = max(len(r) for r in rows)
    padded = [r + [""] * (max_cols - len(r)) for r in rows]
    return pd.DataFrame(padded)

def load_dataframes(file_path_or_obj):
    """Lee CSV o Excel y devuelve una lista de DataFrames normalizados."""
    name = (
        file_path_or_obj.filename
        if hasattr(file_path_or_obj, "filename")
        else str(file_path_or_obj)
    ).lower()

    dfs = []
    if name.endswith(".xlsx") or name.endswith(".xls"):
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="Print area cannot be set to Defined name",
                category=UserWarning,
            )
            sheets = pd.read_excel(file_path_or_obj, sheet_name=None, header=None)
        for _, sheet_df in sheets.items():
            if sheet_df is None or sheet_df.empty:
                continue
            dfs.append(_normalize_dataframe(sheet_df))
    else:
        _reset_stream(file_path_or_obj)
        try:
            df = pd.read_csv(
                file_path_or_obj,
                sep=None,
                engine="python",
                encoding="latin1",
                header=None,
                on_bad_lines="error"
            )
        except Exception:
            _reset_stream(file_path_or_obj)
            df = _read_csv_loose(file_path_or_obj)
        dfs.append(_normalize_dataframe(df))
    return dfs


# ==============================
# 🧩 LÓGICA DE IMPORTACIÓN
# ==============================

def import_rows(df, target, mapping, source=None):
    """
    df         → DataFrame ya cargado
    target     → 'inventario' | 'licencias' | 'empleados'
    mapping    → {col_original: canonical or None}
    """
    conn = db_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS import_unmapped (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT,
            source TEXT,
            row_index INTEGER,
            payload TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    inserted = 0
    updated = 0
    errors = []
    staged = 0

    # columnas canonicas que realmente usaremos
    used_cols = [c for c in mapping.values() if c is not None]

    if not used_cols:
        errors.append("No se reconoció ninguna columna relevante.")
        conn.close()
        return inserted, updated, errors, staged

    for idx, row in df.iterrows():
        data = {}
        extras = {}
        for col_orig, canonical in mapping.items():
            if canonical is None:
                val_extra = row.get(col_orig)
                if pd.notna(val_extra):
                    extras[col_orig] = str(val_extra).strip()
                continue
            val = row.get(col_orig)
            if pd.isna(val):
                continue
            data[canonical] = str(val).strip()

        if not data and not extras:
            continue

        if extras:
            cur.execute(
                "INSERT INTO import_unmapped (target, source, row_index, payload) VALUES (?, ?, ?, ?)",
                (target, source or "", idx + 1, json.dumps(extras, ensure_ascii=False))
            )
            staged += 1

        if extras:
            if target == "inventario" or "observaciones" in data:
                existing = data.get("observaciones", "")
                extra_text = " | ".join(f"{k}:{v}" for k, v in extras.items())
                data["observaciones"] = (existing + " " + extra_text).strip()

        try:
            if target == "inventario":
                inserted, updated = import_inventario_row(cur, data, inserted, updated)
            elif target == "licencias":
                inserted, updated = import_licencia_row(cur, data, inserted, updated)
            elif target == "empleados":
                inserted, updated = import_empleado_row(cur, data, inserted, updated)
            elif target == "bajas":
                inserted, updated = import_baja_row(cur, data, inserted, updated)
            elif target == "insumos":
                inserted, updated = import_insumo_row(cur, data, inserted, updated)
            elif target == "tandas":
                inserted, updated = import_tanda_row(cur, data, inserted, updated)
            elif target == "sedes":
                inserted, updated = import_sede_row(cur, data, inserted, updated)
            elif target == "inventario_administrativo":
                inserted, updated = import_admin_row(cur, data, inserted, updated)
            else:
                errors.append(f"Destino no soportado: {target}")
        except Exception as e:
            errors.append(f"Fila {idx+1}: {e}")

    conn.commit()
    conn.close()
    return inserted, updated, errors, staged


def import_inventario_row(cur, data, inserted, updated):
    """Inserta/actualiza en equipos_individuales."""
    key = data.get('codigo_barras_individual') or data.get('serial')
    if not key:
        return inserted, updated

    # Filtrar a columnas reales de la tabla para evitar errores (ej: 'ubicacion' inexistente)
    valid_cols = _get_table_columns(cur, 'equipos_individuales')
    data = {k: v for k, v in data.items() if k in valid_cols}
    if not data:
        return inserted, updated

    cur.execute(
        'SELECT id FROM equipos_individuales WHERE codigo_barras_individual=? OR serial=?',
        (key, key)
    )
    row = cur.fetchone()

    if row:
        cols = ', '.join([f"{k}=?" for k in data.keys()])
        cur.execute(
            f'UPDATE equipos_individuales SET {cols} WHERE id=?',
            list(data.values()) + [row['id']]
        )
        updated += 1
    else:
        cols = ', '.join(data.keys())
        qs = ', '.join(['?'] * len(data))
        cur.execute(
            f'INSERT INTO equipos_individuales ({cols}) VALUES ({qs})',
            list(data.values())
        )
        inserted += 1

    return inserted, updated

def import_licencia_row(cur, data, inserted, updated):
    key = data.get("email")
    if not key:
        return inserted, updated

    cur.execute(
        "SELECT id FROM licencias_office365 WHERE email=?",
        (key,)
    )
    row = cur.fetchone()

    if row:
        cols = ", ".join([f"{k}=?" for k in data.keys()])
        cur.execute(
            f"UPDATE licencias_office365 SET {cols} WHERE id=?",
            list(data.values()) + [row["id"]]
        )
        updated += 1
    else:
        cols = ", ".join(data.keys())
        qs = ", ".join(["?"] * len(data))
        cur.execute(
            f"INSERT INTO licencias_office365 ({cols}) VALUES ({qs})",
            list(data.values())
        )
        inserted += 1

    return inserted, updated


def import_empleado_row(cur, data, inserted, updated):
    key = data.get("cedula")
    if not key:
        return inserted, updated

    cur.execute(
        "SELECT id FROM empleados WHERE cedula=?",
        (key,)
    )
    row = cur.fetchone()

    if row:
        cols = ", ".join([f"{k}=?" for k in data.keys()])
        cur.execute(
            f"UPDATE empleados SET {cols} WHERE id=?",
            list(data.values()) + [row["id"]]
        )
        updated += 1
    else:
        cols = ", ".join(data.keys())
        qs = ", ".join(["?"] * len(data))
        cur.execute(
            f"INSERT INTO empleados ({cols}) VALUES ({qs})",
            list(data.values())
        )
        inserted += 1

    return inserted, updated


def import_baja_row(cur, data, inserted, updated):
    equipo_key = data.get("codigo_barras_individual") or data.get("serial")
    tipo_inv = data.get("tipo_inventario") or data.get("tecnologia")
    if not tipo_inv:
        tipo_inv = "inventario_general"

    equipo_id = None
    if equipo_key:
        cur.execute(
            "SELECT id FROM equipos_individuales WHERE codigo_barras_individual=? OR serial=?",
            (equipo_key, equipo_key)
        )
        r = cur.fetchone()
        if r:
            equipo_id = r["id"]

    cols = ["equipo_id", "tipo_inventario", "motivo_baja", "responsable_baja", "documentos_soporte", "fotografias_soporte", "observaciones"]
    vals = [
        equipo_id,
        tipo_inv,
        data.get("motivo_baja"),
        data.get("responsable_baja"),
        data.get("documentos_soporte"),
        data.get("fotografias_soporte"),
        data.get("observaciones")
    ]
    cur.execute(
        f"INSERT INTO inventario_bajas ({', '.join(cols)}) VALUES ({', '.join(['?']*len(cols))})",
        vals
    )
    inserted += 1
    return inserted, updated


def import_insumo_row(cur, data, inserted, updated):
    mapped = {
        "nombre_insumo": data.get("nombre_insumo"),
        "serial_equipo": data.get("serial_equipo"),
        "cantidad_total": data.get("cantidad_total"),
        "cantidad_disponible": data.get("cantidad_total"),
        "ubicacion": data.get("ubicacion"),
        "asignado_a": data.get("asignado_a"),
        "creador_registro": data.get("creador_registro") or "IMPORTADOR",
        "observaciones": data.get("observaciones"),
    }
    cols = ", ".join(mapped.keys())
    qs = ", ".join(["?"] * len(mapped))
    cur.execute(
        f"INSERT INTO insumos ({cols}) VALUES ({qs})",
        list(mapped.values())
    )
    inserted += 1
    return inserted, updated


def import_sede_row(cur, data, inserted, updated):
    """Inserta/actualiza en sedes."""
    codigo = data.get("codigo_sede") or data.get("codigo") or data.get("codigo_unificado")
    nombre = data.get("nombre_sede") or data.get("sede") or data.get("nombre")
    if not (codigo or nombre):
        return inserted, updated

    cur.execute(
        "SELECT id FROM sedes WHERE codigo=? OR nombre=? LIMIT 1",
        (codigo, nombre)
    )
    row = cur.fetchone()
    cols = []
    vals = []
    for k, v in data.items():
        cols.append(k)
        vals.append(v)
    if row:
        set_clause = ", ".join([f"{k}=?" for k in data.keys()])
        cur.execute(f"UPDATE sedes SET {set_clause} WHERE id=?", vals + [row["id"]])
        updated += 1
    else:
        placeholders = ", ".join(["?"] * len(cols))
        cur.execute(f"INSERT INTO sedes ({', '.join(cols)}) VALUES ({placeholders})", vals)
        inserted += 1
    return inserted, updated


def import_admin_row(cur, data, inserted, updated):
    """Inserta en inventario_administrativo (muebles)."""
    key = data.get("codigo_interno")
    cur.execute("SELECT id FROM inventario_administrativo WHERE codigo_interno=?", (key,))
    row = cur.fetchone()
    cols = list(data.keys())
    vals = list(data.values())
    if row:
        set_clause = ", ".join([f"{k}=?" for k in cols])
        cur.execute(f"UPDATE inventario_administrativo SET {set_clause} WHERE id=?", vals + [row["id"]])
        updated += 1
    else:
        placeholders = ", ".join(["?"] * len(cols))
        cur.execute(f"INSERT INTO inventario_administrativo ({', '.join(cols)}) VALUES ({placeholders})", vals)
        inserted += 1
    return inserted, updated


def import_tanda_row(cur, data, inserted, updated):
    mapped = {
        "numero_tanda": data.get("numero_tanda"),
        "descripcion": data.get("descripcion"),
        "cantidad_equipos": data.get("cantidad_equipos"),
        "proveedor": data.get("proveedor"),
        "valor_total": data.get("valor_total"),
        "observaciones": data.get("observaciones"),
    }
    cols = ", ".join(mapped.keys())
    qs = ", ".join(["?"] * len(mapped))
    cur.execute(
        f"INSERT INTO tandas_equipos_nuevos ({cols}) VALUES ({qs})",
        list(mapped.values())
    )
    inserted += 1
    return inserted, updated


# ==============================
# 🌐 RUTAS FLASK
# ==============================

@export_import_bp.route("/", methods=["GET"])
def importar_form():
    return redirect(url_for("export_import_v2.importar_form"))


@export_import_bp.route("/preview", methods=["POST"])
def importar_preview():
    return redirect(url_for("export_import_v2.importar_preview"))


@export_import_bp.route("/procesar", methods=["POST"])
def importar_procesar():
    return redirect(url_for("export_import_v2.importar_procesar"))


# ==============================
# 📤 EXPORTADORES UNIVERSALES
# ==============================

@export_import_bp.route("/exportar/<destino>")
def exportar(destino):
    conn = db_conn()
    if destino == "inventario":
        query = "SELECT * FROM equipos_individuales"
        filename = "inventario_tecnologico.csv"
    elif destino == "licencias":
        query = "SELECT * FROM licencias_office365"
        filename = "licencias_office365.csv"
    elif destino == "empleados":
        query = "SELECT * FROM empleados"
        filename = "empleados.csv"
    else:
        conn.close()
        flash("Destino de exportación no soportado.", "danger")
        return redirect(url_for("export_import.importar_form"))

    df = pd.read_sql_query(query, conn)
    conn.close()

    export_path = os.path.join(TMP_DIR, filename)
    df.to_csv(export_path, index=False, encoding="utf-8-sig")

    return send_file(
        export_path,
        as_attachment=True,
        download_name=filename,
        mimetype="text/csv"
    )
