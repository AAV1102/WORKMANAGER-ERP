"""
Sistema Maestro de Inventario para WorkManager ERP
Módulo avanzado de gestión de inventario con funcionalidades completas
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
import glob
import subprocess
import sys
from flask import Blueprint, render_template, jsonify, request, current_app, send_from_directory

class InventarioMaestro:
    """
    Clase principal para gestión avanzada de inventario
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "..", "..", "workmanager_erp.db")
        self._ensure_connection()

    def _ensure_connection(self):
        """Asegura que la conexión a la base de datos esté disponible"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            raise ConnectionError(f"No se pudo conectar a la base de datos: {e}")

    def get_estadisticas_completas(self) -> Dict[str, Any]:
        """Obtiene estadísticas completas del inventario"""
        try:
            cursor = self.conn.cursor()

            # Estadísticas generales
            stats = {
                'total_equipos': 0,
                'equipos_individuales': 0,
                'equipos_agrupados': 0,
                'equipos_disponibles': 0,
                'equipos_asignados': 0,
                'equipos_baja': 0,
                'por_tecnologia': {},
                'por_sede': {},
                'por_estado': {}
            }

            # Conteo de equipos individuales
            cursor.execute("SELECT COUNT(*) FROM equipos_individuales")
            stats['equipos_individuales'] = cursor.fetchone()[0]

            # Conteo de equipos agrupados
            cursor.execute("SELECT COUNT(*) FROM equipos_agrupados")
            stats['equipos_agrupados'] = cursor.fetchone()[0]

            stats['total_equipos'] = stats['equipos_individuales'] + stats['equipos_agrupados']

            # Estadísticas por estado (individuales)
            cursor.execute("""
                SELECT estado, COUNT(*) as cantidad
                FROM equipos_individuales
                GROUP BY estado
            """)
            for row in cursor.fetchall():
                estado = row[0] or 'sin_estado'
                stats['por_estado'][estado] = row[1]
                if estado.lower() == 'disponible':
                    stats['equipos_disponibles'] += row[1]
                elif estado.lower() == 'asignado':
                    stats['equipos_asignados'] += row[1]
                elif estado.lower() == 'baja':
                    stats['equipos_baja'] += row[1]

            # Estadísticas por tecnología
            cursor.execute("""
                SELECT tecnologia, COUNT(*) as cantidad
                FROM equipos_individuales
                WHERE tecnologia IS NOT NULL AND tecnologia != ''
                GROUP BY tecnologia
                ORDER BY cantidad DESC
            """)
            for row in cursor.fetchall():
                stats['por_tecnologia'][row[0]] = row[1]

            # Estadísticas por sede
            cursor.execute("""
                SELECT s.nombre, COUNT(ei.id) as cantidad
                FROM equipos_individuales ei
                LEFT JOIN sedes s ON ei.sede_id = s.id
                GROUP BY s.nombre
                ORDER BY cantidad DESC
            """)
            for row in cursor.fetchall():
                sede = row[0] or 'Sin sede asignada'
                stats['por_sede'][sede] = row[1]

            return stats

        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {}

    def buscar_equipos_avanzado(self, filtros: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Búsqueda avanzada de equipos con múltiples criterios"""
        try:
            cursor = self.conn.cursor()

            query = """
                SELECT ei.*,
                       s.nombre as sede_nombre,
                       s.ciudad as sede_ciudad
                FROM equipos_individuales ei
                LEFT JOIN sedes s ON ei.sede_id = s.id
                WHERE 1=1
            """
            params = []

            # Aplicar filtros
            if filtros.get('serial'):
                query += " AND ei.serial LIKE ?"
                params.append(f"%{filtros['serial']}%")

            if filtros.get('codigo_barras_individual'):
                query += " AND ei.codigo_barras_individual LIKE ?"
                params.append(f"%{filtros['codigo_barras_individual']}%")

            if filtros.get('tecnologia'):
                query += " AND ei.tecnologia LIKE ?"
                params.append(f"%{filtros['tecnologia']}%")

            if filtros.get('marca'):
                query += " AND ei.marca LIKE ?"
                params.append(f"%{filtros['marca']}%")

            if filtros.get('estado'):
                query += " AND ei.estado LIKE ?"
                params.append(f"%{filtros['estado']}%")

            if filtros.get('sede_id'):
                query += " AND ei.sede_id = ?"
                params.append(filtros['sede_id'])

            if filtros.get('asignado_nuevo'):
                query += " AND ei.asignado_nuevo LIKE ?"
                params.append(f"%{filtros['asignado_nuevo']}%")

            # Ordenar por fecha de creación descendente
            query += " ORDER BY ei.fecha_creacion DESC"

            # Limitar resultados si se especifica
            if filtros.get('limit'):
                query += " LIMIT ?"
                params.append(filtros['limit'])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            resultados = []
            for row in rows:
                equipo = dict(row)
                # Agregar información adicional
                equipo['tipo'] = 'individual'
                equipo['sede_completa'] = f"{equipo.get('sede_nombre', '')} - {equipo.get('sede_ciudad', '')}".strip(' - ')
                resultados.append(equipo)

            return resultados

        except Exception as e:
            print(f"Error en búsqueda avanzada: {e}")
            return []

    def importar_desde_excel(self, filepath: str, hoja: str = None) -> Dict[str, Any]:
        """Importa datos desde archivo Excel con mapeo inteligente"""
        try:
            # Leer archivo Excel
            if hoja:
                df = pd.read_excel(filepath, sheet_name=hoja)
            else:
                df = pd.read_excel(filepath)

            # Detectar encabezados automáticamente
            header_row = self._detectar_encabezados(df)
            if header_row > 0:
                df.columns = df.iloc[header_row]
                df = df.iloc[header_row + 1:].reset_index(drop=True)

            # Limpiar nombres de columnas
            df.columns = df.columns.str.strip().str.upper()

            # Mapear columnas automáticamente
            mapeo_columnas = self._mapear_columnas_automatico(df.columns.tolist())

            # Crear DataFrame procesado
            df_procesado = pd.DataFrame()
            for col_db, posibles_nombres in mapeo_columnas.items():
                for nombre_excel in posibles_nombres:
                    if nombre_excel in df.columns:
                        df_procesado[col_db] = df[nombre_excel].astype(str).str.strip()
                        break

            # Agregar metadatos
            df_procesado['fecha_creacion'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df_procesado['creador_registro'] = 'IMPORTADOR_MAESTRO'

            # Generar códigos de barras si no existen
            if 'codigo_barras_individual' not in df_procesado.columns or df_procesado['codigo_barras_individual'].isna().all():
                contador = self._obtener_ultimo_contador()
                df_procesado['codigo_barras_individual'] = [
                    self._generar_codigo_barras(row.get('tecnologia'), contador + i)
                    for i, row in df_procesado.iterrows()
                ]

            # Insertar en base de datos
            registros_insertados = self._insertar_dataframe(df_procesado)

            return {
                'exito': True,
                'registros_insertados': registros_insertados,
                'total_filas': len(df_procesado),
                'mensaje': f'Importación exitosa: {registros_insertados} registros insertados'
            }

        except Exception as e:
            return {
                'exito': False,
                'error': str(e),
                'mensaje': f'Error en importación: {str(e)}'
            }

    def _detectar_encabezados(self, df: pd.DataFrame, max_filas: int = 10) -> int:
        """Detecta automáticamente la fila de encabezados"""
        for i in range(min(max_filas, len(df))):
            fila = df.iloc[i]
            no_vacios = fila.notna().sum()
            if no_vacios > len(fila) * 0.4:  # Al menos 40% de celdas no vacías
                texto_fila = ' '.join(fila.astype(str).str.upper())
                palabras_clave = ['SERIAL', 'PLACA', 'MARCA', 'MODELO', 'TECNOLOGIA']
                if any(palabra in texto_fila for palabra in palabras_clave):
                    return i
        return 0

    def _mapear_columnas_automatico(self, columnas_excel: List[str]) -> Dict[str, List[str]]:
        """Mapea automáticamente columnas de Excel a columnas de BD"""
        return {
            'codigo_barras_individual': ['CODIGO', 'CODIGO BARRAS', 'PLACA', 'CODIGO_INDIVIDUAL'],
            'tecnologia': ['TECNOLOGIA', 'TIPO', 'TIPO EQUIPO', 'DESCRIPCION'],
            'serial': ['SERIAL', 'SERIE', 'NUMERO SERIE'],
            'placa': ['PLACA', 'PLACA No.', 'NUMERO PLACA'],
            'marca': ['MARCA', 'FABRICANTE', 'BRAND'],
            'modelo': ['MODELO', 'MODEL'],
            'procesador': ['PROCESADOR', 'CPU'],
            'cantidad_ram': ['RAM', 'MEMORIA', 'CANTIDAD RAM'],
            'tipo_disco': ['TIPO DISCO', 'TIPO DE DISCO'],
            'espacio_disco': ['DISCO', 'ALMACENAMIENTO', 'STORAGE'],
            'so': ['SO', 'SISTEMA OPERATIVO', 'OS'],
            'ip': ['IP', 'IP ADDRESS'],
            'mac': ['MAC', 'MAC ADDRESS'],
            'hostname': ['HOSTNAME', 'HOST NAME'],
            'asignado_nuevo': ['ASIGNADO A', 'USUARIO', 'ASIGNADO'],
            'estado': ['ESTADO', 'STATUS', 'CONDICION'],
            'observaciones': ['OBSERVACIONES', 'NOTAS', 'COMENTARIOS']
        }

    def _obtener_ultimo_contador(self) -> int:
        """Obtiene el último contador de códigos de barras"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM equipos_individuales")
        return cursor.fetchone()[0]

    def _generar_codigo_barras(self, tecnologia: str, contador: int) -> str:
        """Genera código de barras único basado en tecnología"""
        mapeo_tech = {
            'PORTATIL': 'PORT', 'LAPTOP': 'PORT',
            'PC ESCRITORIO': 'DESK', 'DESKTOP': 'DESK',
            'TODO EN UNO': 'AIO', 'ALL IN ONE': 'AIO',
            'MONITOR': 'MON', 'PANTALLA': 'MON',
            'IMPRESORA': 'IMP', 'PRINTER': 'IMP',
            'TELEFONO': 'TEL', 'PHONE': 'TEL',
            'SERVIDOR': 'SRV', 'SERVER': 'SRV'
        }

        tech_upper = str(tecnologia).upper() if tecnologia else 'GEN'
        codigo_tech = 'GEN'

        for tech, codigo in mapeo_tech.items():
            if tech in tech_upper:
                codigo_tech = codigo
                break

        return f"{codigo_tech}-{str(contador).zfill(4)}"

    def _insertar_dataframe(self, df: pd.DataFrame, chunk_size: int = 500) -> int:
        """Inserta DataFrame en la base de datos por lotes"""
        cursor = self.conn.cursor()
        total_insertados = 0

        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i+chunk_size]

            for _, row in chunk.iterrows():
                # Preparar datos para inserción
                columnas = [col for col in row.index if pd.notna(row[col])]
                valores = [row[col] for col in columnas]

                placeholders = ', '.join(['?' for _ in columnas])
                columnas_str = ', '.join(columnas)

                try:
                    cursor.execute(
                        f"INSERT INTO equipos_individuales ({columnas_str}) VALUES ({placeholders})",
                        valores
                    )
                    total_insertados += 1
                except sqlite3.IntegrityError:
                    # Código duplicado, intentar actualizar
                    if 'codigo_barras_individual' in columnas:
                        codigo = row.get('codigo_barras_individual')
                        if codigo:
                            set_clause = ', '.join([f"{col} = ?" for col in columnas if col != 'codigo_barras_individual'])
                            valores_update = [row[col] for col in columnas if col != 'codigo_barras_individual']
                            valores_update.append(codigo)

                            try:
                                cursor.execute(
                                    f"UPDATE equipos_individuales SET {set_clause} WHERE codigo_barras_individual = ?",
                                    valores_update
                                )
                            except Exception:
                                pass  # Ignorar errores de actualización
                except Exception:
                    continue  # Ignorar otros errores

            self.conn.commit()

        return total_insertados

    def generar_reporte_completo(self, formato: str = 'json') -> str:
        """Genera reporte completo del inventario"""
        estadisticas = self.get_estadisticas_completas()

        if formato.lower() == 'json':
            return json.dumps(estadisticas, indent=2, ensure_ascii=False)
        elif formato.lower() == 'html':
            return self._generar_reporte_html(estadisticas)
        else:
            return str(estadisticas)

    def _generar_reporte_html(self, stats: Dict[str, Any]) -> str:
        """Genera reporte en formato HTML"""
        html = f"""
        <html>
        <head>
            <title>Reporte Maestro de Inventario</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .stats {{ display: flex; flex-wrap: wrap; gap: 20px; }}
                .stat-card {{ border: 1px solid #ddd; padding: 15px; border-radius: 5px; min-width: 200px; }}
                .stat-number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Reporte Maestro de Inventario - WorkManager ERP</h1>
            <p>Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

            <div class="stats">
                <div class="stat-card">
                    <h3>Total Equipos</h3>
                    <div class="stat-number">{stats.get('total_equipos', 0)}</div>
                </div>
                <div class="stat-card">
                    <h3>Equipos Individuales</h3>
                    <div class="stat-number">{stats.get('equipos_individuales', 0)}</div>
                </div>
                <div class="stat-card">
                    <h3>Equipos Disponibles</h3>
                    <div class="stat-number">{stats.get('equipos_disponibles', 0)}</div>
                </div>
                <div class="stat-card">
                    <h3>Equipos Asignados</h3>
                    <div class="stat-number">{stats.get('equipos_asignados', 0)}</div>
                </div>
            </div>

            <h2>Equipos por Tecnología</h2>
            <table>
                <tr><th>Tecnología</th><th>Cantidad</th></tr>
                {"".join(f"<tr><td>{tech}</td><td>{count}</td></tr>" for tech, count in stats.get('por_tecnologia', {}).items())}
            </table>

            <h2>Equipos por Sede</h2>
            <table>
                <tr><th>Sede</th><th>Cantidad</th></tr>
                {"".join(f"<tr><td>{sede}</td><td>{count}</td></tr>" for sede, count in stats.get('por_sede', {}).items())}
            </table>
        </body>
        </html>
        """
        return html

    def __del__(self):
        """Cierra la conexión al destruir el objeto"""
        if hasattr(self, 'conn'):
            self.conn.close()


# ============================== Blueprint UI ===============================
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NOTEBOOK_GLOB = os.path.join(PROJECT_ROOT, "*.ipynb")
# Rutas actualizadas: usamos la carpeta uploads del proyecto como origen y guardamos el log en logs/
IMPORT_SOURCE = os.path.join(PROJECT_ROOT, "uploads")
IMPORT_SCRIPT = os.path.join(PROJECT_ROOT, "scripts", "inventario", "importador_masivo_workmanager.py")
IMPORT_LOG = os.path.join(PROJECT_ROOT, "logs", "importador_maestro.log")

inventario_maestro_bp = Blueprint(
    "inventario_maestro",
    __name__,
    template_folder="../templates",
    static_folder="../static",
    url_prefix="/inventario-maestro",
)


def _get_maestro_instance():
    return InventarioMaestro(db_path=os.path.join(PROJECT_ROOT, "workmanager_erp.db"))


@inventario_maestro_bp.route("/", methods=["GET"])
def inventario_maestro_home():
    maestro = _get_maestro_instance()
    stats = maestro.get_estadisticas_completas()
    notebooks = sorted(glob.glob(NOTEBOOK_GLOB))
    return render_template(
        "inventario_maestro.html",
        stats=stats,
        notebooks=[os.path.basename(n) for n in notebooks],
        import_script=os.path.relpath(IMPORT_SCRIPT, PROJECT_ROOT),
        import_source=IMPORT_SOURCE,
    )


@inventario_maestro_bp.route("/api/stats", methods=["GET"])
def inventario_maestro_stats():
    maestro = _get_maestro_instance()
    return jsonify(maestro.get_estadisticas_completas())


@inventario_maestro_bp.route("/api/import", methods=["POST"])
def inventario_maestro_import():
    """Dispara el importador masivo en segundo plano y devuelve el log path."""
    if not os.path.exists(IMPORT_SCRIPT):
        return jsonify({"error": "No se encontró el script de importación masiva"}), 404

    os.makedirs(os.path.dirname(IMPORT_LOG), exist_ok=True)

    with open(IMPORT_LOG, "a", encoding="utf-8") as log_file:
        log_file.write(f"\n{'='*60}\nLanzando importador {datetime.now()}\n")
    try:
        subprocess.Popen(
            [sys.executable, IMPORT_SCRIPT],
            cwd=PROJECT_ROOT,
            stdout=open(IMPORT_LOG, "a", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            shell=False,
        )
    except Exception as exc:
        return jsonify({"error": f"No se pudo lanzar el importador: {exc}"}), 500

    return jsonify({"message": "Importador lanzado", "log": os.path.relpath(IMPORT_LOG, PROJECT_ROOT)})


@inventario_maestro_bp.route("/api/import/log", methods=["GET"])
def inventario_maestro_import_log():
    if not os.path.exists(IMPORT_LOG):
        return jsonify({"log": ""})
    try:
        with open(IMPORT_LOG, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()[-200:]
        return jsonify({"log": "".join(lines)})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@inventario_maestro_bp.route("/notebooks/<path:filename>", methods=["GET"])
def inventario_maestro_notebook(filename):
    """Permite descargar notebooks .ipynb desde la raíz del proyecto."""
    if not filename.endswith(".ipynb"):
        return jsonify({"error": "Solo se permiten archivos .ipynb"}), 400
    notebook_path = os.path.join(PROJECT_ROOT)
    full_path = os.path.abspath(os.path.join(notebook_path, filename))
    if not full_path.startswith(notebook_path):
        return jsonify({"error": "Ruta inválida"}), 400
    if not os.path.exists(full_path):
        return jsonify({"error": "Archivo no encontrado"}), 404
    return send_from_directory(notebook_path, filename, as_attachment=True)
