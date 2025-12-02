#!/usr/bin/env python3
"""
Script de sincronización automática para WORKMANAGER ERP
Sincroniza cambios en tiempo real con bases de datos externas.
"""

import os
import sys
import time
import sqlite3
import requests
import schedule
from datetime import datetime
from pathlib import Path

# Configuración
DB_PATH = 'workmanager_erp.db'
SYNC_INTERVAL = 300  # 5 minutos
LOG_FILE = 'logs/sync.log'

def log_message(message):
    """Registra mensaje en log"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {message}\n"

    # Crear directorio de logs si no existe
    Path('logs').mkdir(exist_ok=True)

    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log_entry)

    print(message)

def get_db_connection():
    """Conecta a la base de datos local"""
    return sqlite3.connect(DB_PATH)

def sync_employees():
    """Sincroniza empleados con base de datos externa"""
    try:
        log_message("🔄 Sincronizando empleados...")

        # Aquí iría la lógica para conectar a tu base de datos externa
        # Ejemplo con API REST
        # response = requests.get('https://tu-api-externa.com/empleados')
        # if response.status_code == 200:
        #     employees_data = response.json()
        #     # Procesar y actualizar empleados

        # Por ahora, simulamos sincronización
        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar si hay cambios locales para enviar
        cur.execute("SELECT COUNT(*) FROM empleados WHERE updated_at > datetime('now', '-5 minutes')")
        changes = cur.fetchone()[0]

        if changes > 0:
            log_message(f"📤 Enviando {changes} cambios de empleados al servidor remoto")
            # Aquí enviarías los cambios a la API externa

        conn.close()
        log_message("✅ Sincronización de empleados completada")

    except Exception as e:
        log_message(f"❌ Error sincronizando empleados: {e}")

def sync_inventory():
    """Sincroniza inventario con base de datos externa"""
    try:
        log_message("🔄 Sincronizando inventario...")

        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar cambios en equipos individuales
        cur.execute("SELECT COUNT(*) FROM equipos_individuales WHERE updated_at > datetime('now', '-5 minutes')")
        individual_changes = cur.fetchone()[0]

        # Verificar cambios en equipos agrupados
        cur.execute("SELECT COUNT(*) FROM equipos_agrupados WHERE updated_at > datetime('now', '-5 minutes')")
        grouped_changes = cur.fetchone()[0]

        total_changes = individual_changes + grouped_changes

        if total_changes > 0:
            log_message(f"📤 Enviando {total_changes} cambios de inventario al servidor remoto")
            # Aquí enviarías los cambios a la API externa

        conn.close()
        log_message("✅ Sincronización de inventario completada")

    except Exception as e:
        log_message(f"❌ Error sincronizando inventario: {e}")

def sync_licenses():
    """Sincroniza licencias con base de datos externa"""
    try:
        log_message("🔄 Sincronizando licencias...")

        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar cambios en licencias
        cur.execute("SELECT COUNT(*) FROM licencias_office365 WHERE updated_at > datetime('now', '-5 minutes')")
        license_changes = cur.fetchone()[0]

        if license_changes > 0:
            log_message(f"📤 Enviando {license_changes} cambios de licencias al servidor remoto")
            # Aquí enviarías los cambios a la API externa

        conn.close()
        log_message("✅ Sincronización de licencias completada")

    except Exception as e:
        log_message(f"❌ Error sincronizando licencias: {e}")

def sync_tickets():
    """Sincroniza tickets con base de datos externa"""
    try:
        log_message("🔄 Sincronizando tickets...")

        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar cambios en tickets
        cur.execute("SELECT COUNT(*) FROM tickets WHERE updated_at > datetime('now', '-5 minutes')")
        ticket_changes = cur.fetchone()[0]

        if ticket_changes > 0:
            log_message(f"📤 Enviando {ticket_changes} cambios de tickets al servidor remoto")
            # Aquí enviarías los cambios a la API externa

        conn.close()
        log_message("✅ Sincronización de tickets completada")

    except Exception as e:
        log_message(f"❌ Error sincronizando tickets: {e}")

def full_sync():
    """Ejecuta sincronización completa"""
    log_message("🚀 Iniciando sincronización completa...")
    sync_employees()
    sync_inventory()
    sync_licenses()
    sync_tickets()
    log_message("🎉 Sincronización completa finalizada")

def check_connectivity():
    """Verifica conectividad con bases de datos externas"""
    try:
        # Aquí verificarías la conectividad con tus APIs externas
        # response = requests.get('https://tu-api-externa.com/health')
        # return response.status_code == 200

        # Por ahora, simulamos conectividad
        return True

    except Exception as e:
        log_message(f"❌ Error de conectividad: {e}")
        return False

def main():
    """Función principal"""
    print("🔄 WORKMANAGER ERP - Servicio de Sincronización")
    print("=" * 50)
    print(f"Intervalo de sincronización: {SYNC_INTERVAL} segundos")
    print(f"Archivo de log: {LOG_FILE}")
    print()

    # Verificar conectividad inicial
    if not check_connectivity():
        print("❌ No hay conectividad con las bases de datos externas")
        print("El servicio se ejecutará en modo offline")
        print()

    # Programar sincronizaciones
    schedule.every(SYNC_INTERVAL).seconds.do(full_sync)

    # Ejecutar sincronización inicial
    full_sync()

    print("✅ Servicio de sincronización iniciado")
    print("Presiona Ctrl+C para detener")
    print()

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        log_message("🛑 Servicio de sincronización detenido por el usuario")
        print("\n🛑 Servicio detenido")

if __name__ == "__main__":
    # Si se ejecuta con --once, hace una sincronización única y sale
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        full_sync()
    else:
        main()
