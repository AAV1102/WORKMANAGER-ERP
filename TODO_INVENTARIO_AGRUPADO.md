# TODO: Implementación de Inventario Agrupado

## Información Recopilada
- Sistema actual tiene inventario individual y agrupado separado
- Necesita flujo integrado para crear paquetes agrupados
- Códigos: MED(SEDE)-AGRU-XXX para unificado, MED(SEDE)-TIP-XXX para individuales
- Búsqueda de componentes por serial, placa, código barras, hostname
- Asignación con búsqueda por cédula, usuario Windows, ID, nombre completo

## Plan de Implementación

### 1. Modificar Template Principal (inventarios_clean.html)
- Agregar pestaña "Crear Agrupado" con selector de tipo de equipo
- Implementar flujo paso a paso: seleccionar tipo -> buscar componentes -> crear paquete

### 2. Crear Nuevo Template (new_inventario_agrupado.html)
- Selector de tipo de equipo (monitor, CPU, portátil, etc.)
- Para cada tipo, mostrar campos de búsqueda específicos
- Interfaz para agregar componentes encontrados
- Generación automática de código unificado

### 3. Actualizar Backend (inventarios_updated.py)
- Nueva ruta `/inventarios/new_agrupado`
- Lógica para buscar componentes por criterios específicos por tipo
- Generación de códigos consecutivos automática
- Asociación de componentes al paquete agrupado

### 4. Modificar Asignación (assign_inventario_updated.html)
- Agregar búsqueda por cédula, usuario Windows, ID, nombre completo
- Integrar con API de búsqueda de empleados

### 5. Actualizar API de Búsqueda
- Endpoint para buscar empleados por múltiples criterios
- Endpoint para buscar componentes disponibles por tipo

### 6. Generación de Códigos
- Función para generar códigos MED(SEDE)-AGRU-XXX
- Función para códigos individuales MED(SEDE)-TIP-XXX
- Contadores automáticos por sede

### 7. Testing y Validación
- Verificar flujo completo de creación
- Validar asignaciones
- Probar generación de códigos

## Dependencias
- Requiere tablas existentes: equipos_agrupados, equipos_individuales, equipos_componentes, empleados, sedes
- Necesita campos adicionales si faltan (hostname, etc.)

## Próximos Pasos
1. Crear template new_inventario_agrupado.html
2. Implementar lógica backend para creación agrupada
3. Actualizar búsqueda de asignación
4. Probar integración completa
