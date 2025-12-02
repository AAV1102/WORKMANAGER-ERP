# TODO: Organizar y Completar Módulos de Inventarios, Licencias, Sedes y Gestión Humana

## ✅ **COMPLETADO**
- [x] Análisis de módulos existentes
- [x] Identificación de duplicados y funcionalidades faltantes

## 🔄 **TAREAS PENDIENTES - ALTA PRIORIDAD**

### 1. **Consolidar Módulos de Inventarios**
- [ ] Eliminar módulos duplicados: `inventario_individual.py`, `inventario_agrupado.py`, `inventarios_updated.py`, `inventario_tecnologico.py`, `inventarios.py` (mantener solo `inventarios.py` como principal)
- [ ] Consolidar todas las rutas en `modules/inventarios.py`
- [ ] Unificar templates: mantener `inventarios_clean.html` como principal, eliminar duplicados
- [ ] Completar CRUD para equipos agrupados e individuales
- [ ] Implementar asignaciones entre empleados y equipos
- [ ] Agregar búsqueda avanzada por sede, empleado, serial, etc.

### 2. **Completar Módulo de Sedes**
- [ ] Agregar CRUD completo (crear, editar, eliminar sedes)
- [ ] Integrar con inventarios (mostrar equipos por sede)
- [ ] Integrar con empleados (asignar empleados a sedes)
- [ ] Agregar estadísticas por sede
- [ ] Mejorar template `sede_detail.html`

### 3. **Integrar Gestión Humana con Otros Módulos**
- [ ] Conectar empleados con sedes (campo sede_id)
- [ ] Integrar asignaciones de equipos a empleados
- [ ] Conectar licencias con empleados
- [ ] Agregar reportes de RRHH por sede
- [ ] Completar solicitudes RRHH

### 4. **Completar Módulo de Licencias**
- [ ] Agregar asignación manual de licencias a empleados
- [ ] Integrar con sedes (licencias por sede)
- [ ] Agregar gestión de vencimientos
- [ ] Mejorar importación de CSV
- [ ] Agregar reportes de uso

### 5. **Actualizar App.py y Rutas**
- [ ] Registrar todos los blueprints correctamente
- [ ] Eliminar rutas duplicadas
- [ ] Asegurar que todas las rutas funcionen
- [ ] Actualizar imports

### 6. **Actualizar Templates y UI**
- [ ] Actualizar sidebar con enlaces correctos
- [ ] Completar formularios faltantes
- [ ] Agregar botones de acción (editar, eliminar, asignar)
- [ ] Mejorar dashboards con estadísticas
- [ ] Unificar estilos en `base.html`

### 7. **Implementar Asignaciones Cruzadas**
- [ ] Asignar equipos a empleados desde inventarios
- [ ] Asignar empleados a sedes desde gestión humana
- [ ] Asignar licencias a empleados desde licencias
- [ ] Validar integridad de datos en asignaciones

### 8. **Limpiar Código y Eliminar Duplicados**
- [ ] Eliminar archivos innecesarios
- [ ] Consolidar funciones similares
- [ ] Optimizar consultas a BD
- [ ] Agregar manejo de errores

### 9. **Testing y Validación**
- [ ] Probar todas las rutas
- [ ] Validar formularios
- [ ] Probar asignaciones
- [ ] Verificar integridad de BD

### 10. **Preparar para Producción**
- [ ] Agregar logging
- [ ] Optimizar performance
- [ ] Agregar validaciones de seguridad
- [ ] Documentar APIs

## 📋 **DEPENDENCIAS**
- SQLite database existente
- Flask blueprints
- Templates Jinja2

## 🔧 **ARCHIVOS PRINCIPALES A MODIFICAR**
- `modules/inventarios.py` (consolidar)
- `modules/sedes.py` (completar)
- `modules/gestion_humana.py` (integrar)
- `modules/licencias.py` (completar)
- `app.py` (rutas)
- Templates: `inventarios_clean.html`, `sede_detail.html`, `gestion_humana.html`, `licencias.html`, `base.html`

## 📊 **PROGRESO**
- **Módulos Analizados:** 4/4
- **Duplicados Identificados:** 5+
- **Rutas por Completar:** 20+
- **Templates por Actualizar:** 10+

---
**Prioridad:** Consolidar inventarios → Completar sedes → Integrar asignaciones → Actualizar UI → Testing
