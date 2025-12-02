# TODO Tracker

Todas las tareas en un único punto de referencia, para poder planificar y atacar cada módulo. La idea es ir marcando avances aquí mismo conforme las tareas se completan.

## Prioridad inmediata

1. **Gestión Humana completa**
   - Revisar `gestion_humana.py` y `templates/empleado_editar.html` para que todos los campos (usuario Windows, código biométrico, código unificado, trazabilidad administrativa, observaciones, roles y permisos) estén disponibles y se sincronicen con inventarios/licencias (`inventarios.py`, `licencias.py`).
   - Revisar las vistas `templates/gestion_humana.html`, `templates/empleado_detalle.html` y `templates/hoja_vida_empleado.html` para mostrar los campos extra, las acciones que faltan (ver perfil, asignar equipo/licencia, generar reportes) y enlazar con los nuevos endpoints (`export_import_updated.py`, `inventarios.py`).
   - Conectar los botones de asignar/buscar (equipos/licencias/usuarios) con APIs REST (ej. `/inventarios/api/search_users`, `/licencias/api/search_users`) y permitir crear empleados temporales si no existen.

2. **Sedes y trazabilidad por sede**
   - Asegurar `modules/sedes.py` y `templates/sede_detail.html` muestran inventario tecnológico (agrupado, individual, por ciudad), licencias, tickets y empleados filtrados por sede, incluyendo información de roles/usuario/estado.
   - Añadir capacidades de asignar usuarios/licencias/inventarios por sede y generar códigos agrupados automáticamente basados en los datos de inventario general.
   - Vincular la mesa de ayuda (`templates/mesa_ayuda.html`, `modules/mesa_ayuda.py`) para que los tickets aparezcan filtrados por sede y se puedan enlazar con empleados/equipos concretos.

3. **Inventario General + Importadores**
   - Consolidar los importadores existentes (`inventario_import`, `export_import`, `export_import_updated`) en el nuevo panel centralizado, eliminando duplicaciones, e incorporar detección automática, preview y exportes personalizados por módulo (inventario, licencias, empleados, accesories, bajas).
   - Actualizar los botones del sidebar, dashboard y módulos (`templates/base.html`, `templates/workmanager_dashboard.html`, `templates/inventario_general.html`, etc.) para que apuntan al importador universal y dejan claro los formatos admitidos.
   - Revolver los errores pasados (“Formato image no soportado”, “table importador”) asegurando los endpoints de exportación manejan `fmt=image` y regresan datos significativos.

4. **API / acciones de inventario**
   - Completar los endpoints faltantes en `modules/inventarios.py`: asignaciones, reasignaciones, búsqueda, hoja de vida, reporte, trazabilidad y botones (equipos repotenciados, préstamos, telemedicina, D2K y DME, componentes adicionales, tecnología).
   - Conectar los tabs “Equipos agrupados / individuales / por sede / por usuario / por área” con datos reales en tiempo real, generando tablas y filtros desde el inventario general (incluyendo “Equipos Asignados”, “Equipos Dados de Baja”, “Tandas Nuevas”).
   - Añadir botones en la UI que disparan las APIs (mostrar en `templates/inventarios.html`, `templates/inventarios_fixed.html`) y enlazar con roles/permisos del empleado actual.

5. **AI / Reportes / Solicitudes**
   - Garantizar las APIs de IA (`ai_service.py`, `templates/ai_service.html`) siempre reciben `inventory_agent_stats` y cuentan consultas de inventario/rrhh. Mostrar log de consultas y validaciones de performance.
   - Completar los reportes/solicitudes en RRHH: formularios `templates/solicitudes_rrhh.html`, `templates/reportes_rrhh.html`, `templates/solicitud_detalle.html`, endpoints de aprobación/rechazo, generación de reportes y exportes (PDF/Excel).
   - Vincular las solicitudes/reportes con las acciones de mesa de ayuda y la hoja de vida para trazar estado, performance, aprobaciones y contrapartes (inventario/licencias).

6. **Sincronización con licencias y mesa de ayuda**
   - Garantizar `modules/licencias.py` está enlazado con empleados (nombre completo, sede) y se pueden asignar licencias desde el panel de empleados.
   - Botones de mesa de ayuda deben generar tickets contextualizados con el equipo/usuario seleccionado y mostrar filtros (por estado, sede, tipo).
   - Permitir exportaciones filtradas (CSV/Excel) desde los reportes de RRHH/mesa de ayuda según los campos seleccionados (cedula, usuario Windows, Quirón, biometría, licencias/equipos asignados).

## Seguimiento

- Usar este archivo (`todo.md`) como documento vivo y actualizar el estado (`en progreso`, `hecho`, etc.) junto con referencias a commits y archivos modificados.  
- Priorizar los módulos más críticos en este orden: RRHH → Inventarios → Sedes → Licencias/Mesa de ayuda → AI/Reporte/Exportadores.


## Estado actual

- [x] Gesti?n Humana sincronizada con inventarios/licencias, incluyendo asignaciones directas y paneles din?micos.
- [x] Importadores/exportadores consolidados en `export_import_v2` y redirecciones limpias.
- [x] Sedes y mesa de ayuda enriquecidas con datos reales, filtros y vistas conectadas.
- [x] AI, reportes y tecnolog?as de inventario completadas (eventos de pesta?as, dashboards y m?tricas).
