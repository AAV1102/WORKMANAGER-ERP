# Mesa de ayuda, asignaciones y agente inteligente

Este documento resume el estado actual de las funciones a las que haces referencia y propone los pasos necesarios para conectar todo en tiempo real.

## Mesa de ayuda

- El blueprint `modules/mesa_ayuda.py` expone rutas `/mesa_ayuda`, `/ticket/new`, `/ticket/<id>/edit`, `/ticket/<id>/delete` y la API `/api/tickets`. Cada ruta trabaja sobre la tabla `tickets` de `workmanager_erp.db` y usa los templates `mesa_ayuda.html`, `new_ticket.html` y `edit_ticket.html`.
- Cuando visitas `/mesa_ayuda` ves el listado ordenado por `created_at`; cada formulario escribe directamente en la base de datos. Si necesitas integrarlo con canales adicionales (WhatsApp, correo, etc.), hay dos caminos claros:
 1. Crear un servicio que inserte automáticamente tickets personalizados en la misma tabla.
 2. Añadir webhooks o workers que consulten `/api/tickets` para sincronizar estados.

## Botón “Asignar equipos” en empleados

- La vista `templates/users.html` (ej.: botones dentro del `table` y la función `asignarEquiposSeleccionados`) solo muestra `alert()`; no hay interacción con el backend.
- Para que la pantalla de empleados sepa a qué equipo asignaste a qué usuario se debe:
 1. Definir una ruta que reciba `user_id` y la lista de `equipo_id` (por ejemplo, un nuevo endpoint en `modules/inventarios.py` o `modules/asignaciones.py`).
 2. Validar que los registros `equipos_individuales` y `empleados` existan y luego insertar registros en `asignaciones_equipos` (o en otra tabla de relación).
 3. Actualizar la IU para mostrar estado y eliminar el uso del `alert()` fijo.
- Mientras esa lógica no exista, el mensaje “Asignando equipos a X usuarios” es solo un placeholder, razón por la cual no ves cambios en la base de datos.

## Servicio de IA y bot de WhatsApp

- El blueprint `modules/ai_service.py` mantiene logs (`ai_logs`) y muestra estadísticas ficticias (por ejemplo, `whatsapp_status = "Activo"` y un diccionario `inventory_agent_stats`). No hay integración real con WhatsApp ni con un bot.
- Para “configurar en tiempo real el bot de WhatsApp” necesitas:
 1. Conectar el archivo `credentials_config.py` (u otro archivo seguro) con tu proveedor (Meta, Twilio, etc.).
 2. Crear endpoints webhook que reciban mensajes y los escriban en `ai_logs` o creen tickets/asignaciones.
 3. Añadir un worker que consuma eventos de la cola y luego actualice estados en vivo.

## Agente de inventario desplegable

Para construir un agente que puedas instalar en cada equipo y que sincronice en tiempo real con `workmanager_erp.db`, proponemos la siguiente arquitectura mínima:

1. **Componente local (Windows/PowerShell o Python).**
   - Monitoriza hardware (serial, placa, usuario logueado, apps instaladas, IP) mediante `wmic`, `systeminfo`, `psutil`, etc.
   - Cada cierto intervalo (ej. 60 s) compara el estado actual con la última entrada local y sólo envía cambios.
   - Siempre que haya cambios, llama a una API REST de la app central.

2. **API central en `modules/inventarios.py`.**
   - Añadir rutas como `/inventarios/api/actualizar` que acepten `POST` con JSON (serial, estado, ubicación, usuario, timestamp).
   - Registrar cada actualización en las tablas `equipos_individuales` y `ai_logs` (o crear `inventory_agent_events` con `status`, `payload`, `created_at`).
   - Guardar en `workmanager_erp.db` junto con la información del equipo.

3. **Sincronización de bases.**
   - Cada instalación del agente puede enviar datos directamente contra el SQLite local si está en la misma red compartida; de lo contrario, exponer una API con autenticación por token (ver `modules/credentials_config.py`).
   - Para “información en tiempo real” puedes complementar con un WebSocket (ej. `Flask-SocketIO`) o un worker que emita eventos con la librería `broadcast`.

4. **Instalación en cada equipo.**
   - Entregar un script tipo `inventario_agent.py` que pueda ejecutarse como servicio o tarea programada.
   - Incluir un archivo de configuración (`agent_config.json`) con la URL del servidor, intervalos, token y rutas de log.
   - Instrucciones típicas: instalar Python 3.11+, crear virtual env, `pip install -r requirements-agent.txt`, copiar `agent_config.json`, ejecutar `python inventario_agent.py --install-service`.

## Próximos pasos sugeridos

1. Extender `templates/users.html` y los blueprints (`modules/user.py`, `modules/asignaciones.py` o `modules/inventarios.py`) para implementar la lógica real de asignaciones.
2. Definir la API REST del agente de inventario y registrarla en la base de datos (`inventarios` + `ai_logs`/`inventory_agent_events`).
3. Crear el script de agente y documentar cómo desplegarlo con autenticación y sincronización en tiempo real.

Si prefieres, puedo ayudarte a construir uno de esos pasos concretos (por ejemplo, crear el endpoint `/inventarios/api/actualizar` o el script del agente). Solo dime por cuál empezamos.
