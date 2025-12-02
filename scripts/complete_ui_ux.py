#!/usr/bin/env python3
"""
Script para completar la UI/UX de WORKMANAGER ERP
Actualiza menús, placeholders, botones, CSS global, footer, etc.
"""

import os
import re
from pathlib import Path

def update_base_template():
    """Actualiza el template base con mejoras de UI/UX"""
    base_path = 'templates/base.html'

    if not os.path.exists(base_path):
        print(f"❌ Template base no encontrado: {base_path}")
        return False

    with open(base_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Agregar más iconos y mejorar navegación
    improvements = {
        # Mejorar sidebar con más módulos
        '<!-- Gestión Humana -->': '''<!-- Gestión Humana -->
        <div class="sidebar-section">
            <a href="#gestionHumanaSubmenu" data-bs-toggle="collapse" class="dropdown-toggle">
                <i class="fas fa-users"></i> Gestión Humana
            </a>
            <div class="collapse show" id="gestionHumanaSubmenu">
                <a href="{{ url_for('user.users') }}" class="submenu-item">
                    <i class="fas fa-list"></i> Empleados
                </a>
                <a href="{{ url_for('user.new_user') }}" class="submenu-item">
                    <i class="fas fa-plus"></i> Nuevo Empleado
                </a>
                <a href="{{ url_for('gestion_humana.dashboard_gestion_humana') }}#solicitudes" class="submenu-item">
                    <i class="fas fa-clipboard-list"></i> Solicitudes
                </a>
                <a href="{{ url_for('gestion_humana.dashboard_gestion_humana') }}#performance" class="submenu-item">
                    <i class="fas fa-chart-line"></i> Performance
                </a>
                <a href="{{ url_for('gestion_humana.dashboard_gestion_humana') }}#reportes" class="submenu-item">
                    <i class="fas fa-file-alt"></i> Reportes RRHH
                </a>
                <a href="{{ url_for('empleados_bp.empleados') }}" class="submenu-item">
                    <i class="fas fa-address-book"></i> Directorio
                </a>
                <a href="#" class="submenu-item">
                    <i class="fas fa-boxes"></i> Inventario Asignado
                </a>
            </div>
        </div>''',

        # Mejorar Inventario Tecnológico
        '<!-- Inventario Tecnológico -->': '''<!-- Inventario Tecnológico -->
        <div class="sidebar-section">
            <a href="#inventarioSubmenu" data-bs-toggle="collapse" class="dropdown-toggle">
                <i class="fas fa-boxes"></i> Inventario Tecnológico
            </a>
            <div class="collapse show" id="inventarioSubmenu">
                <a href="{{ url_for('inventarios.inventarios') }}" class="submenu-item">
                    <i class="fas fa-list"></i> Ver Inventario
                </a>
                <a href="{{ url_for('inventarios.new_inventario') }}" class="submenu-item">
                    <i class="fas fa-plus"></i> Nuevo Equipo Individual
                </a>
                <a href="{{ url_for('inventario_tecnologico.inventario_agrupado') }}" class="submenu-item">
                    <i class="fas fa-layer-group"></i> Equipos Agrupados
                </a>
                <a href="{{ url_for('inventario_general.dashboard_inventario') }}" class="submenu-item">
                    <i class="fas fa-search"></i> Inventario General
                </a>
                <a href="{{ url_for('inventario_tecnologico.equipo_form', equipo_id=0) }}" class="submenu-item">
                    <i class="fas fa-edit"></i> Gestionar Equipos
                </a>
                <a href="#" class="submenu-item">
                    <i class="fas fa-file-alt"></i> Hoja de Vida
                </a>
                <a href="#" class="submenu-item">
                    <i class="fas fa-exchange-alt"></i> Movimientos
                </a>
            </div>
        </div>''',

        # Mejorar Sistemas
        '<!-- Sistemas -->': '''<!-- Sistemas -->
        <div class="sidebar-section">
            <a href="#sistemasSubmenu" data-bs-toggle="collapse" class="dropdown-toggle">
                <i class="fas fa-server"></i> Sistemas
            </a>
            <div class="collapse show" id="sistemasSubmenu">
                <a href="{{ url_for('sistemas.sistemas') }}" class="submenu-item">
                    <i class="fas fa-tachometer-alt"></i> Dashboard Sistemas
                </a>
                <a href="{{ url_for('mesa_ayuda.mesa_ayuda') }}" class="submenu-item">
                    <i class="fas fa-headset"></i> Mesa de Ayuda
                </a>
                <a href="{{ url_for('licencias.dashboard_licencias') }}" class="submenu-item">
                    <i class="fas fa-key"></i> Licencias Office 365
                </a>
                <a href="{{ url_for('ai_service.ai_service') }}" class="submenu-item">
                    <i class="fas fa-robot"></i> AI Service
                </a>
                <a href="#" class="submenu-item">
                    <i class="fas fa-server"></i> Infraestructura
                </a>
                <a href="#" class="submenu-item">
                    <i class="fas fa-eye"></i> Monitoreo
                </a>
                <a href="#" class="submenu-item">
                    <i class="fas fa-shield-alt"></i> Seguridad
                </a>
            </div>
        </div>''',

        # Mejorar Administración
        '<!-- Administración -->': '''<!-- Administración -->
        <div class="sidebar-section">
            <a href="#adminSubmenu" data-bs-toggle="collapse" class="dropdown-toggle">
                <i class="fas fa-cog"></i> Administración
            </a>
            <div class="collapse show" id="adminSubmenu">
                <a href="{{ url_for('admin.admin') }}" class="submenu-item">
                    <i class="fas fa-tachometer-alt"></i> Panel Administrativo
                </a>
                <a href="{{ url_for('admin.inventario_administrativo') }}" class="submenu-item">
                    <i class="fas fa-couch"></i> Inventario Administrativo
                </a>
                <a href="{{ url_for('admin.insumos') }}" class="submenu-item">
                    <i class="fas fa-tools"></i> Insumos
                </a>
                <a href="{{ url_for('admin.facturas') }}" class="submenu-item">
                    <i class="fas fa-file-invoice-dollar"></i> Facturas
                </a>
                <a href="{{ url_for('admin.garantias') }}" class="submenu-item">
                    <i class="fas fa-shield-alt"></i> Garantías
                </a>
                <a href="{{ url_for('admin.proveedores') }}" class="submenu-item">
                    <i class="fas fa-truck"></i> Proveedores
                </a>
                <a href="{{ url_for('sedes.sedes') }}" class="submenu-item">
                    <i class="fas fa-building"></i> Sedes
                </a>
                <a href="{{ url_for('compras_bp.compras') }}" class="submenu-item">
                    <i class="fas fa-shopping-cart"></i> Compras
                </a>
            </div>
        </div>''',

        # Mejorar footer
        '<footer class="bg-dark text-light mt-5 py-4">': '''<footer class="bg-dark text-light mt-5 py-4">
    <div class="container">
        <div class="row">
            <div class="col-md-3">
                <h5>WORKMANAGER ERP</h5>
                <p class="small">Sistema integral de gestión empresarial para optimizar procesos y recursos.</p>
                <div class="social-links">
                    <a href="#" class="text-light me-2"><i class="fab fa-facebook"></i></a>
                    <a href="#" class="text-light me-2"><i class="fab fa-twitter"></i></a>
                    <a href="#" class="text-light me-2"><i class="fab fa-linkedin"></i></a>
                </div>
            </div>
            <div class="col-md-3">
                <h6>Soporte</h6>
                <ul class="list-unstyled">
                    <li><a href="{{ url_for('mesa_ayuda.mesa_ayuda') }}" class="text-light text-decoration-none"><i class="fas fa-headset"></i> Mesa de Ayuda</a></li>
                    <li><a href="mailto:soporte@workmanager.com" class="text-light text-decoration-none"><i class="fas fa-envelope"></i> Contacto</a></li>
                    <li><a href="#" class="text-light text-decoration-none"><i class="fas fa-question-circle"></i> FAQ</a></li>
                    <li><a href="#" class="text-light text-decoration-none"><i class="fas fa-book"></i> Documentación</a></li>
                </ul>
            </div>
            <div class="col-md-3">
                <h6>Módulos</h6>
                <ul class="list-unstyled">
                    <li><a href="{{ url_for('user.users') }}" class="text-light text-decoration-none"><i class="fas fa-users"></i> Gestión Humana</a></li>
                    <li><a href="{{ url_for('inventarios.inventarios') }}" class="text-light text-decoration-none"><i class="fas fa-boxes"></i> Inventario</a></li>
                    <li><a href="{{ url_for('sistemas.sistemas') }}" class="text-light text-decoration-none"><i class="fas fa-server"></i> Sistemas</a></li>
                    <li><a href="{{ url_for('medico.medico') }}" class="text-light text-decoration-none"><i class="fas fa-stethoscope"></i> Médico</a></li>
                </ul>
            </div>
            <div class="col-md-3">
                <h6>Información</h6>
                <ul class="list-unstyled">
                    <small>
                        <li>Versión: 3.0.0</li>
                        <li>© 2024 WORKMANAGER ERP</li>
                        <li>Todos los derechos reservados</li>
                        <li><a href="#" class="text-light text-decoration-none">Política de Privacidad</a></li>
                        <li><a href="#" class="text-light text-decoration-none">Términos de Uso</a></li>
                    </small>
                </ul>
            </div>
        </div>
        <hr class="my-3">
        <div class="row">
            <div class="col-12 text-center">
                <small class="text-muted">
                    Desarrollado con <i class="fas fa-heart text-danger"></i> para optimizar la gestión empresarial
                </small>
            </div>
        </div>
    </div>
</footer>'''
    }

    for old, new in improvements.items():
        if old in content:
            content = content.replace(old, new)

    # Agregar estilos adicionales
    additional_css = '''
        .sidebar .submenu-item:hover {
            background-color: #6c757d;
            padding-left: 45px;
        }

        .navbar-brand {
            font-weight: bold;
            background: linear-gradient(45deg, #007bff, #28a745);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .btn-custom {
            border-radius: 25px;
            padding: 8px 20px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .btn-custom:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }

        .card {
            border: none;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }

        .card:hover {
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }

        .stats-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
        }

        .stats-card .card-title {
            font-size: 0.9rem;
            opacity: 0.9;
        }

        .stats-card h3 {
            font-size: 2rem;
            font-weight: bold;
        }

        .social-links a {
            font-size: 1.2rem;
            transition: all 0.3s ease;
        }

        .social-links a:hover {
            transform: scale(1.2);
        }
    '''

    # Agregar CSS adicional antes del cierre de </style>
    if '</style>' in content:
        content = content.replace('</style>', additional_css + '\n    </style>')

    with open(base_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ Template base actualizado con mejoras de UI/UX")
    return True

def update_global_css():
    """Actualiza el CSS global"""
    css_path = 'static/css/style.css'

    # Crear directorio si no existe
    Path('static/css').mkdir(parents=True, exist_ok=True)

    additional_css = '''
/* WORKMANAGER ERP - Estilos Globales Mejorados */

:root {
    --primary-color: #007bff;
    --secondary-color: #6c757d;
    --success-color: #28a745;
    --danger-color: #dc3545;
    --warning-color: #ffc107;
    --info-color: #17a2b8;
    --light-color: #f8f9fa;
    --dark-color: #343a40;
    --border-radius: 10px;
    --box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    --transition: all 0.3s ease;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f8f9fa;
    color: #333;
    line-height: 1.6;
}

/* Sidebar improvements */
.sidebar {
    background: linear-gradient(180deg, #343a40 0%, #495057 100%);
    box-shadow: 2px 0 10px rgba(0,0,0,0.1);
}

.sidebar a {
    color: #adb5bd;
    text-decoration: none;
    transition: var(--transition);
    border-radius: 5px;
    margin: 2px 10px;
}

.sidebar a:hover {
    color: #fff;
    background-color: rgba(255,255,255,0.1);
    transform: translateX(5px);
}

/* Content area */
.content {
    background-color: #f8f9fa;
    min-height: calc(100vh - 76px);
}

/* Cards */
.card {
    border: none;
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
    transition: var(--transition);
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

.card-header {
    background: linear-gradient(90deg, #007bff, #0056b3);
    color: white;
    border-radius: var(--border-radius) var(--border-radius) 0 0 !important;
    border: none;
}

/* Buttons */
.btn {
    border-radius: 25px;
    padding: 8px 20px;
    font-weight: 500;
    transition: var(--transition);
    border: none;
}

.btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.btn-primary {
    background: linear-gradient(45deg, #007bff, #0056b3);
}

.btn-success {
    background: linear-gradient(45deg, #28a745, #1e7e34);
}

.btn-danger {
    background: linear-gradient(45deg, #dc3545, #bd2130);
}

.btn-warning {
    background: linear-gradient(45deg, #ffc107, #e0a800);
}

.btn-info {
    background: linear-gradient(45deg, #17a2b8, #138496);
}

/* Forms */
.form-control {
    border-radius: 8px;
    border: 2px solid #e9ecef;
    transition: var(--transition);
    padding: 10px 15px;
}

.form-control:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 0.2rem rgba(0, 123, 255, 0.25);
}

/* Tables */
.table {
    border-radius: var(--border-radius);
    overflow: hidden;
    box-shadow: var(--box-shadow);
}

.table thead th {
    background: linear-gradient(90deg, #007bff, #0056b3);
    color: white;
    border: none;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.85rem;
    letter-spacing: 0.5px;
}

.table tbody tr:hover {
    background-color: rgba(0,123,255,0.05);
    transform: scale(1.01);
    transition: var(--transition);
}

/* Alerts */
.alert {
    border-radius: var(--border-radius);
    border: none;
    box-shadow: var(--box-shadow);
}

/* Badges */
.badge {
    border-radius: 20px;
    font-weight: 500;
    padding: 6px 12px;
}

/* Navigation tabs */
.nav-tabs .nav-link {
    border: none;
    border-radius: var(--border-radius) var(--border-radius) 0 0;
    color: #6c757d;
    font-weight: 500;
    transition: var(--transition);
}

.nav-tabs .nav-link.active {
    background: linear-gradient(90deg, #007bff, #0056b3);
    color: white;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

/* Progress bars */
.progress {
    height: 8px;
    border-radius: 10px;
    background-color: #e9ecef;
}

.progress-bar {
    border-radius: 10px;
    background: linear-gradient(90deg, #28a745, #20c997);
}

/* Loading spinner */
.spinner-border {
    color: var(--primary-color);
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.fade-in {
    animation: fadeIn 0.5s ease-in-out;
}

/* Responsive improvements */
@media (max-width: 768px) {
    .sidebar {
        position: fixed;
        top: 0;
        left: -250px;
        width: 250px;
        height: 100vh;
        z-index: 1000;
        transition: left 0.3s ease;
    }

    .sidebar.show {
        left: 0;
    }

    .content {
        margin-left: 0;
        padding-top: 70px;
    }

    .navbar-toggler {
        display: block;
    }
}

/* Custom utilities */
.text-gradient {
    background: linear-gradient(45deg, #007bff, #28a745);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.shadow-custom {
    box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
}

.border-custom {
    border: 2px solid rgba(0,123,255,0.1) !important;
}

/* Notification styles */
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 9999;
    max-width: 400px;
}

.notification .alert {
    margin-bottom: 10px;
    animation: slideInRight 0.3s ease;
}

@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 0;
    }
}

/* Print styles */
@media print {
    .sidebar, .navbar, footer, .btn {
        display: none !important;
    }

    .content {
        margin-left: 0 !important;
        padding: 0 !important;
    }

    .card {
        box-shadow: none !important;
        border: 1px solid #ddd !important;
    }
}
'''

    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(additional_css)

    print("✅ CSS global actualizado con estilos modernos")
    return True

def update_placeholders_and_buttons():
    """Actualiza placeholders y botones en templates"""
    templates_dir = Path('templates')

    if not templates_dir.exists():
        print("❌ Directorio templates no encontrado")
        return False

    # Buscar y actualizar templates
    for template_file in templates_dir.glob('*.html'):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()

            modified = False

            # Mejorar placeholders
            placeholder_improvements = {
                'placeholder="Buscar"': 'placeholder="🔍 Buscar..."',
                'placeholder="Nombre"': 'placeholder="👤 Ingrese el nombre"',
                'placeholder="Email"': 'placeholder="📧 correo@ejemplo.com"',
                'placeholder="Cédula"': 'placeholder="🆔 Número de cédula"',
                'placeholder="Teléfono"': 'placeholder="📞 Número de teléfono"',
                'placeholder="Dirección"': 'placeholder="🏠 Dirección completa"',
                'placeholder="Buscar por serial"': 'placeholder="🔢 Buscar por serial..."',
                'placeholder="Buscar por hostname"': 'placeholder="💻 Buscar por hostname..."',
                'placeholder="Buscar por usuario"': 'placeholder="👤 Buscar por usuario..."',
            }

            for old, new in placeholder_improvements.items():
                if old in content:
                    content = content.replace(old, new)
                    modified = True

            # Mejorar botones
            button_improvements = {
                'class="btn btn-primary"': 'class="btn btn-primary btn-custom"',
                'class="btn btn-success"': 'class="btn btn-success btn-custom"',
                'class="btn btn-danger"': 'class="btn btn-danger btn-custom"',
                'class="btn btn-warning"': 'class="btn btn-warning btn-custom"',
                'class="btn btn-info"': 'class="btn btn-info btn-custom"',
            }

            for old, new in button_improvements.items():
                if old in content:
                    content = content.replace(old, new)
                    modified = True

            # Agregar clases de animación a cards principales
            if '<div class="card">' in content and 'fade-in' not in content:
                content = content.replace(
                    '<div class="card">',
                    '<div class="card fade-in">',
                    1  # Solo la primera ocurrencia
                )
                modified = True

            if modified:
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Actualizado: {template_file.name}")

        except Exception as e:
            print(f"❌ Error actualizando {template_file.name}: {e}")

    return True

def main():
    """Función principal"""
    print("🎨 WORKMANAGER ERP - Completar UI/UX")
    print("=" * 40)

    success = True

    # Actualizar template base
    if not update_base_template():
        success = False

    # Actualizar CSS global
    if not update_global_css():
        success = False

    # Actualizar placeholders y botones
    if not update_placeholders_and_buttons():
        success = False

    if success:
        print("\n✅ UI/UX completada exitosamente")
        print("\n📋 Mejoras implementadas:")
        print("- ✅ Sidebar expandida con todos los módulos")
        print("- ✅ Navegación mejorada con iconos")
        print("- ✅ Footer completo con enlaces y redes sociales")
        print("- ✅ CSS moderno con gradientes y animaciones")
        print("- ✅ Placeholders descriptivos con emojis")
        print("- ✅ Botones con efectos hover")
        print("- ✅ Cards con sombras y transiciones")
        print("- ✅ Diseño responsivo mejorado")
        print("- ✅ Animaciones de carga y transiciones")
        print("\n🎯 La interfaz ahora tiene una apariencia moderna y profesional")
    else:
        print("\n❌ Algunas actualizaciones de UI/UX fallaron")

if __name__ == "__main__":
    main()
