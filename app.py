from datetime import datetime
import logging
import os
import sqlite3
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, g
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from flask_babel import Babel
from werkzeug.security import generate_password_hash, check_password_hash

from config import get_config
from modules.db_utils import (
    get_db_connection,
    load_active_db_path,
    save_active_db_path,
    list_available_dbs,
)
from modules.credentials_config import DEFAULT_ADMIN, DEMO_USER

# Configuración base de la app
config = get_config()
app = Flask(__name__, static_folder="static", static_url_path="/static", template_folder="templates")
app.config.from_object(config)

# --- FIX: Asegurar que el directorio de logs exista ANTES de importar módulos ---
log_dir = os.path.join(app.root_path, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configuración centralizada de Logging
log_file = os.path.join(log_dir, 'app.log')
handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
# --------------------------------------------------------------------

from modules.db_utils import (
    load_active_db_path,
    save_active_db_path,
    list_available_dbs,
)
from modules.credentials_config import DEFAULT_ADMIN, DEMO_USER

# Blueprints principales
from modules import (
    user,
    inventarios,
    sistemas,
    gestion_humana,
    medico,
    biomedica,
    licencias,
    ai_service,
    export_import,
    mesa_ayuda,
    sedes,
    admin,
    auth,
    inventario_general,
    import_inventario_general,
    workmanager_dashboard,
    accesorios,
    bajas,
    import_bajas,
    configuracion,
    infraestructura,
    monitoreo,
    seguridad,
    auto_import,
)
# Otros blueprints
from modules import (
    export_import_updated,
    inventario_maestro,
    extensiones_inventarios,
    logistica,
    juridico,
    tesoreria,
    import_module,
    solicitudes,
    barcodes,
    asset_profile,
    universal_exporter,
    dashboard_manager,
    notifications,
    mantenimientos,
    visualizador_inventario,
    inventory_dashboard,
    inventory_report,
    report_generator,
)
from modules.compras import compras_bp
from modules.import_compras import compras_import_bp
from modules.asignaciones import asignaciones_bp
from modules.import_asignaciones import asignaciones_import_bp
# --------------------------------------------------------------------

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Por favor inicia sesión para acceder a esta página."
login_manager.login_message_category = "info"


class User:
    """Adaptador mínimo para flask-login."""

    def __init__(self, user_data):
        data = dict(user_data)
        self.id = data.get("id")
        self.email = data.get("email")
        self.nombre = data.get("nombre")
        self.apellido = data.get("apellido")
        self.nombre_completo = data.get("nombre_completo") or f"{self.nombre} {self.apellido}".strip()
        self.rol = data.get("rol", "usuario")
        self.estado = data.get("estado", "activo")

    def get_id(self):
        """Compatibilidad con flask-login: retorna el id como string."""
        return str(self.id) if self.id is not None else None

    def is_active(self):
        return (self.estado or "").lower() == "activo"

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False


@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
    user_data = c.fetchone()
    conn.close()
    if user_data:
        return User(user_data)
    return None


# --- CONFIGURACIÓN AVANZADA DE PLANTILLAS ---
# (Reservado para blueprints extra si se habilitan en el futuro)
# ---------------------------------------------

# Internacionalización
LANGUAGES = ["es", "en"]


def get_locale():
    """Obtiene el idioma actual y lo almacena en g."""
    if "lang" in session:
        g.locale = session["lang"]
        return session["lang"]
    g.locale = request.accept_languages.best_match(LANGUAGES)
    return g.locale


babel = Babel(app, locale_selector=get_locale)


# Ruta para que el usuario cambie de idioma
@app.route("/lang/<language>")
def set_language(language=None):
    if language in LANGUAGES:
        session["lang"] = language
    return redirect(request.referrer or url_for("index"))


@app.context_processor
def inject_global_data():
    """
    Inyecta datos globales en todas las plantillas.
    Ahora 'sedes' y 'LANGUAGES' estarán disponibles en cualquier archivo HTML.
    """
    try:
        conn = get_db_connection()
        sedes = conn.execute("SELECT id, nombre FROM sedes ORDER BY nombre").fetchall()

        # Contar solicitudes pendientes para notificaciones (solo para admins)
        pending_requests = 0
        if current_user.is_authenticated and hasattr(current_user, "rol") and current_user.rol == "admin":
            try:
                pending_requests = (
                    conn.execute("SELECT COUNT(id) FROM solicitudes WHERE estado = 'pendiente'").fetchone()[0]
                )
            except sqlite3.OperationalError:
                pending_requests = 0

        conn.close()
        return dict(
            sedes=sedes,
            LANGUAGES=LANGUAGES,
            pending_requests_count=pending_requests,
            current_year=datetime.utcnow().year,
        )
    except Exception:
        return dict(sedes=[], LANGUAGES=LANGUAGES, pending_requests_count=0)


# Registrar blueprints principales
app.register_blueprint(user.user_bp)
app.register_blueprint(inventarios.inventarios_bp)
app.register_blueprint(sistemas.sistemas_bp)
app.register_blueprint(gestion_humana.gestion_humana_bp)
app.register_blueprint(medico.medico_bp)
app.register_blueprint(biomedica.biomedica_bp)
app.register_blueprint(licencias.licencias_bp)
app.register_blueprint(ai_service.ai_service_bp)
app.register_blueprint(export_import.export_import_bp)
app.register_blueprint(export_import_updated.export_import_bp, url_prefix="/export_import")
app.register_blueprint(mesa_ayuda.mesa_ayuda_bp)
app.register_blueprint(sedes.sedes_bp)
app.register_blueprint(admin.admin_bp)
app.register_blueprint(auth.auth_bp)
app.register_blueprint(inventario_general.inventario_general_bp)
app.register_blueprint(import_inventario_general.inventario_import_bp)
app.register_blueprint(workmanager_dashboard.workmanager_dashboard_bp)
app.register_blueprint(accesorios.accesorios_bp)
app.register_blueprint(bajas.bajas_bp)
app.register_blueprint(import_bajas.bajas_import_bp)
app.register_blueprint(compras_bp)
app.register_blueprint(compras_import_bp)
app.register_blueprint(asignaciones_bp)
app.register_blueprint(asignaciones_import_bp)
app.register_blueprint(inventario_maestro.inventario_maestro_bp)
app.register_blueprint(mantenimientos.mantenimientos_bp)

# Otros blueprints registrados
app.register_blueprint(configuracion.configuracion_bp)
app.register_blueprint(infraestructura.infraestructura_bp)
app.register_blueprint(monitoreo.monitoreo_bp)
app.register_blueprint(seguridad.seguridad_bp)
app.register_blueprint(auto_import.auto_import_bp)
app.register_blueprint(extensiones_inventarios.extensiones_bp)
app.register_blueprint(logistica.logistica_bp)
app.register_blueprint(juridico.juridico_bp)
app.register_blueprint(tesoreria.tesoreria_bp)
app.register_blueprint(import_module.import_bp)
app.register_blueprint(solicitudes.solicitudes_bp)
app.register_blueprint(barcodes.barcodes_bp)
app.register_blueprint(asset_profile.asset_profile_bp)
app.register_blueprint(universal_exporter.universal_exporter_bp)
app.register_blueprint(dashboard_manager.dashboard_manager_bp)
app.register_blueprint(notifications.notifications_bp)
app.register_blueprint(inventory_report.inventory_report_bp)
app.register_blueprint(inventory_dashboard.inventory_dashboard_bp)
app.register_blueprint(visualizador_inventario.visualizador_bp)
app.register_blueprint(report_generator.report_generator_bp)


@app.route("/")
def index():
    # El dashboard ahora se carga dinámicamente con JavaScript
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/routes")
def list_routes():
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({"rule": str(rule), "endpoint": rule.endpoint, "methods": list(rule.methods)})
    return jsonify(routes)


# Simple metrics
@app.route("/metrics")
def metrics():
    conn = get_db_connection()
    c = conn.cursor()
    data = {}
    try:
        for table in ["empleados", "equipos_agrupados", "equipos_individuales", "licencias_office365", "facturas", "tickets"]:
            try:
                c.execute(f"SELECT COUNT(*) FROM {table}")
                data[table] = c.fetchone()[0]
            except Exception:
                data[table] = 0
    finally:
        conn.close()
    return jsonify(data)


PROTECTED_ENDPOINTS = {
    "admin.admin": "view_admin",
    "configuracion.configuracion": "manage_config",
}


def user_has_permission(user_id, permission_code):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            """
            SELECT 1
            FROM user_roles ur
            JOIN role_permissions rp ON rp.role_id = ur.role_id
            JOIN permissions p ON p.id = rp.permission_id
            WHERE ur.user_id = ? AND p.code = ?
            LIMIT 1
        """,
            (user_id, permission_code),
        )
        return c.fetchone() is not None
    except Exception:
        return False
    finally:
        conn.close()


@app.before_request
def before():
    # 1. Cargar idioma
    get_locale()

    # 2. Cargar ID de usuario
    g.user_id = current_user.id if current_user.is_authenticated else session.get("user_id")
    endpoint = request.endpoint

    # 3. Proteger rutas para el usuario DEMO
    if current_user.is_authenticated and getattr(current_user, "rol", "") == "demo":
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            flash("La cuenta demo es solo lectura.", "warning")
            return redirect(request.referrer or url_for("index"))

    # 4. Proteger rutas por permisos
    if endpoint in PROTECTED_ENDPOINTS:
        required = PROTECTED_ENDPOINTS[endpoint]
        if not g.user_id or not user_has_permission(g.user_id, required):
            flash("No tienes permiso para acceder a esta área.", "danger")
            return redirect(url_for("auth.login"))
    app.logger.info(f"REQ {endpoint}")


@app.after_request
def after(resp):
    app.logger.info(f"RESP {resp.status_code}")
    return resp


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
    except Exception:
        conn.rollback()
    finally:
        conn.close()


def create_missing_tables():
    """Asegura que todas las tablas necesarias, como 'solicitudes', existan."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS solicitudes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empleado_id INTEGER NOT NULL,
                tipo_solicitud TEXT NOT NULL,
                fecha_inicio DATE,
                fecha_fin DATE,
                descripcion TEXT NOT NULL,
                estado TEXT DEFAULT 'pendiente',
                respuesta_admin TEXT,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (empleado_id) REFERENCES empleados (id)
            );
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notificaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                url TEXT,
                is_read INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES usuarios (id)
            );
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS facturas_proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_factura TEXT UNIQUE NOT NULL,
                proveedor_id INTEGER,
                monto REAL NOT NULL,
                fecha_emision DATE NOT NULL,
                fecha_vencimiento DATE,
                estado TEXT DEFAULT 'pendiente',
                FOREIGN KEY (proveedor_id) REFERENCES proveedores (id)
            );
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contratos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_contrato TEXT UNIQUE NOT NULL,
                nombre_contrato TEXT,
                contraparte TEXT,
                fecha_inicio DATE,
                fecha_fin DATE,
                tipo TEXT,
                estado TEXT DEFAULT 'activo'
            );
        """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ordenes_envio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_guia TEXT UNIQUE NOT NULL,
                transportadora TEXT,
                origen TEXT,
                destino TEXT,
                fecha_envio DATE,
                fecha_entrega_estimada DATE,
                estado TEXT DEFAULT 'en_transito'
            );
        """
        )

        conn.commit()
        print("Tabla 'solicitudes' verificada y/o creada exitosamente.")
    finally:
        conn.close()


# Asegurar inicialización básica aunque se ejecute via run.py
ensure_default_admin()
create_missing_tables()


@app.route("/api/tasks", methods=["GET", "POST"])
def tasks():
    if request.method == "POST":
        data = request.get_json()
        title = data.get("title")
        description = data.get("description")
        conn = sqlite3.connect("todo.db")
        c = conn.cursor()
        c.execute("INSERT INTO tasks (title, description) VALUES (?, ?)", (title, description))
        conn.commit()
        conn.close()
        return jsonify({"message": "Task added successfully"}), 201
    else:
        conn = sqlite3.connect("todo.db")
        c = conn.cursor()
        c.execute("SELECT * FROM tasks")
        tasks = c.fetchall()
        conn.close()
        return jsonify(tasks)


@app.route("/api/tasks/<int:task_id>", methods=["PUT", "DELETE"])
def task(task_id):
    if request.method == "PUT":
        data = request.get_json()
        title = data.get("title")
        description = data.get("description")
        status = data.get("status")
        conn = sqlite3.connect("todo.db")
        c = conn.cursor()
        c.execute(
            "UPDATE tasks SET title=?, description=?, status=? WHERE id=?",
            (title, description, status, task_id),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Task updated successfully"})
    elif request.method == "DELETE":
        conn = sqlite3.connect("todo.db")
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()
        conn.close()
        return jsonify({"message": "Task deleted successfully"})


@app.route("/login", methods=["GET", "POST"])
def login():
    active_db = load_active_db_path()
    db_options = list_available_dbs()

    if request.method == "POST":
        selected_db = request.form.get("db_path") or active_db
        if selected_db and os.path.abspath(selected_db) != os.path.abspath(active_db):
            active_db = save_active_db_path(selected_db)
            init_db()
            ensure_default_admin()

        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM usuarios WHERE email = ? AND estado = 'activo'", (email,))
        user_data = c.fetchone()
        auth_ok = False
        if user_data:
            auth_ok = check_password_hash(user_data["password"], password)

        if not auth_ok:
            c.execute("SELECT * FROM empleados WHERE email = ? AND estado = 'activo'", (email,))
            emp = c.fetchone()
            if emp and (str(emp["cedula"]) == str(password)):
                user_data = {
                    "id": emp["id"],
                    "email": emp["email"],
                    "nombre": emp["nombre"],
                    "apellido": emp["apellido"],
                    "rol": "usuario",
                    "estado": emp["estado"],
                }
                auth_ok = True

        conn.close()

        if auth_ok and user_data:
            user_obj = User(user_data)
            login_user(user_obj)
            session["user_id"] = user_obj.id
            session["db_path"] = active_db
            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for("index"))
        else:
            flash(
                f"Credenciales inválidas. Puedes usar {DEFAULT_ADMIN['email']} / {DEFAULT_ADMIN['password']} o tu correo de empleado + cédula.",
                "danger",
            )

    return render_template(
        "login.html",
        default_admin=DEFAULT_ADMIN,
        demo_user=DEMO_USER,
        db_options=db_options,
        active_db=active_db,
    )


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop("user_id", None)
    session.pop("db_path", None)
    flash("Sesión cerrada exitosamente.", "info")
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        cedula = request.form.get("cedula")
        nombre = request.form.get("nombre")
        apellido = request.form.get("apellido")
        email = request.form.get("email")
        password = request.form.get("password")
        rol = request.form.get("rol", "usuario")

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute(
                """
                INSERT INTO usuarios (cedula, nombre, apellido, nombre_completo, email, password, rol)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (cedula, nombre, apellido, f"{nombre} {apellido}", email, hashed_password, rol),
            )
            conn.commit()
            flash("Usuario registrado exitosamente.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("El email o cédula ya están registrados.", "danger")
        finally:
            conn.close()

    return render_template("register.html")


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.route("/api/delete/<string:table_name>/<int:item_id>", methods=["DELETE"])
@login_required
def delete_item(table_name, item_id):
    """
    API genérica y segura para eliminar un registro de una tabla.
    """
    allowed = ["equipos_individuales", "equipos_agrupados", "empleados", "licencias_office365", "proveedores", "inventario_bajas"]

    if table_name not in allowed:
        return jsonify({"success": False, "error": "Operación no permitida para esta tabla."}), 403

    try:
        conn = get_db_connection()
        conn.execute(f"DELETE FROM {table_name} WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Ítem eliminado correctamente."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
