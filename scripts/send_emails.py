#!/usr/bin/env python3
"""
Script para envío automático de correos en WORKMANAGER ERP
Maneja notificaciones, resets de contraseña, alertas del sistema, etc.
"""

import os
import sys
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

# Configuración de email (debería venir de .env o config)
SMTP_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('MAIL_PORT', 587))
SMTP_USERNAME = os.environ.get('MAIL_USERNAME', '')
SMTP_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
FROM_EMAIL = os.environ.get('MAIL_USERNAME', 'noreply@workmanager.com')

def get_db_connection():
    """Conecta a la base de datos"""
    return sqlite3.connect('workmanager_erp.db')

def send_email(to_email, subject, html_content, text_content=None):
    """Envía un email"""
    try:
        # Crear mensaje
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email

        # Adjuntar contenido HTML
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Adjuntar contenido texto plano si se proporciona
        if text_content:
            text_part = MIMEText(text_content, 'plain')
            msg.attach(text_part)

        # Conectar al servidor SMTP
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        server.quit()

        print(f"✅ Email enviado a {to_email}: {subject}")
        return True

    except Exception as e:
        print(f"❌ Error enviando email a {to_email}: {e}")
        return False

def send_password_reset_email(email, reset_token):
    """Envía email de reset de contraseña"""
    subject = "WORKMANAGER ERP - Reset de Contraseña"

    html_content = f"""
    <html>
    <body>
        <h2>Reset de Contraseña - WORKMANAGER ERP</h2>
        <p>Has solicitado resetear tu contraseña.</p>
        <p>Para crear una nueva contraseña, haz clic en el siguiente enlace:</p>
        <p><a href="http://localhost:5000/reset_password/{reset_token}">Resetear Contraseña</a></p>
        <p>Este enlace expirará en 24 horas.</p>
        <p>Si no solicitaste este reset, ignora este email.</p>
        <br>
        <p>Saludos,<br>Equipo WORKMANAGER ERP</p>
    </body>
    </html>
    """

    text_content = f"""
    WORKMANAGER ERP - Reset de Contraseña

    Has solicitado resetear tu contraseña.
    Para crear una nueva contraseña, visita: http://localhost:5000/reset_password/{reset_token}

    Este enlace expirará en 24 horas.
    Si no solicitaste este reset, ignora este email.

    Saludos,
    Equipo WORKMANAGER ERP
    """

    return send_email(email, subject, html_content, text_content)

def send_welcome_email(email, nombre, temp_password):
    """Envía email de bienvenida con contraseña temporal"""
    subject = f"Bienvenido a WORKMANAGER ERP - {nombre}"

    html_content = f"""
    <html>
    <body>
        <h2>¡Bienvenido a WORKMANAGER ERP!</h2>
        <p>Hola {nombre},</p>
        <p>Tu cuenta ha sido creada exitosamente en WORKMANAGER ERP.</p>
        <p><strong>Credenciales de acceso:</strong></p>
        <ul>
            <li>Email: {email}</li>
            <li>Contraseña temporal: {temp_password}</li>
        </ul>
        <p>Por favor cambia tu contraseña la primera vez que inicies sesión.</p>
        <p><a href="http://localhost:5000/login">Iniciar Sesión</a></p>
        <br>
        <p>Saludos,<br>Equipo WORKMANAGER ERP</p>
    </body>
    </html>
    """

    text_content = f"""
    ¡Bienvenido a WORKMANAGER ERP!

    Hola {nombre},

    Tu cuenta ha sido creada exitosamente.

    Credenciales de acceso:
    - Email: {email}
    - Contraseña temporal: {temp_password}

    Por favor cambia tu contraseña la primera vez que inicies sesión.
    Visita: http://localhost:5000/login

    Saludos,
    Equipo WORKMANAGER ERP
    """

    return send_email(email, subject, html_content, text_content)

def send_ticket_notification(ticket_id, titulo, usuario_asignado_email, usuario_reporta):
    """Envía notificación de nuevo ticket asignado"""
    subject = f"WORKMANAGER ERP - Nuevo Ticket Asignado: #{ticket_id}"

    html_content = f"""
    <html>
    <body>
        <h2>Nuevo Ticket Asignado</h2>
        <p>Se te ha asignado un nuevo ticket:</p>
        <ul>
            <li><strong>ID:</strong> #{ticket_id}</li>
            <li><strong>Título:</strong> {titulo}</li>
            <li><strong>Reportado por:</strong> {usuario_reporta}</li>
        </ul>
        <p><a href="http://localhost:5000/mesa_ayuda">Ver Ticket</a></p>
        <br>
        <p>Saludos,<br>Equipo WORKMANAGER ERP</p>
    </body>
    </html>
    """

    return send_email(usuario_asignado_email, subject, html_content)

def send_inventory_alert(equipo_info, tipo_alerta):
    """Envía alertas de inventario"""
    subject = f"WORKMANAGER ERP - Alerta de Inventario: {tipo_alerta}"

    html_content = f"""
    <html>
    <body>
        <h2>Alerta de Inventario</h2>
        <p>Se ha detectado una alerta en el inventario:</p>
        <ul>
            <li><strong>Tipo:</strong> {tipo_alerta}</li>
            <li><strong>Equipo:</strong> {equipo_info.get('codigo', 'N/A')}</li>
            <li><strong>Marca:</strong> {equipo_info.get('marca', 'N/A')}</li>
            <li><strong>Modelo:</strong> {equipo_info.get('modelo', 'N/A')}</li>
        </ul>
        <p><a href="http://localhost:5000/inventarios">Ver Inventario</a></p>
        <br>
        <p>Saludos,<br>Equipo WORKMANAGER ERP</p>
    </body>
    </html>
    """

    # Enviar a administradores (aquí deberías tener una lista de emails de admin)
    admin_emails = ['admin@workmanager.com']  # Configurable

    success = True
    for admin_email in admin_emails:
        if not send_email(admin_email, subject, html_content):
            success = False

    return success

def process_pending_emails():
    """Procesa emails pendientes en la base de datos"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Obtener emails pendientes
        cur.execute("""
            SELECT * FROM email_queue
            WHERE status = 'pending'
            AND attempts < 3
            ORDER BY created_at ASC
            LIMIT 10
        """)

        pending_emails = cur.fetchall()

        for email_record in pending_emails:
            email_id = email_record['id']
            to_email = email_record['to_email']
            subject = email_record['subject']
            html_content = email_record['html_content']
            text_content = email_record['text_content']
            attempts = email_record['attempts']

            # Intentar enviar
            if send_email(to_email, subject, html_content, text_content):
                # Marcar como enviado
                cur.execute("""
                    UPDATE email_queue
                    SET status = 'sent', sent_at = datetime('now')
                    WHERE id = ?
                """, (email_id,))
            else:
                # Incrementar contador de intentos
                cur.execute("""
                    UPDATE email_queue
                    SET attempts = attempts + 1,
                        last_attempt = datetime('now')
                    WHERE id = ?
                """, (email_id,))

                # Si supera los 3 intentos, marcar como fallido
                if attempts + 1 >= 3:
                    cur.execute("""
                        UPDATE email_queue
                        SET status = 'failed'
                        WHERE id = ?
                    """, (email_id,))

        conn.commit()

        if pending_emails:
            print(f"📧 Procesados {len(pending_emails)} emails pendientes")

    except Exception as e:
        print(f"❌ Error procesando emails pendientes: {e}")
    finally:
        conn.close()

def queue_email(to_email, subject, html_content, text_content=None):
    """Agrega email a la cola de envío"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO email_queue (to_email, subject, html_content, text_content, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (to_email, subject, html_content, text_content))

        conn.commit()
        email_id = cur.lastrowid
        print(f"📧 Email agregado a cola: {email_id}")
        return email_id

    except Exception as e:
        print(f"❌ Error agregando email a cola: {e}")
        return None
    finally:
        conn.close()

def main():
    """Función principal"""
    print("📧 WORKMANAGER ERP - Servicio de Emails")
    print("=" * 40)

    # Verificar configuración SMTP
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print("❌ Configuración SMTP incompleta")
        print("Configura MAIL_USERNAME y MAIL_PASSWORD en tu archivo .env")
        sys.exit(1)

    # Procesar emails pendientes
    process_pending_emails()

    print("✅ Servicio de emails ejecutado")

if __name__ == "__main__":
    # Si se pasan argumentos, procesar comando específico
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'process':
            process_pending_emails()
        elif command == 'test':
            # Email de prueba
            test_email = input("Email de prueba: ")
            send_email(test_email, "WORKMANAGER ERP - Email de Prueba",
                      "<h1>Email de Prueba</h1><p>Este es un email de prueba del sistema WORKMANAGER ERP.</p>")
        else:
            print("Comandos disponibles:")
            print("  process - Procesa emails pendientes")
            print("  test    - Envía email de prueba")
    else:
        main()
