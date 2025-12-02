let dashboardData = null;

function formatEstadoBadge(value) {
    if (!value) return '<span class="badge bg-light text-dark">N/A</span>';
    const normalized = value.toString().toLowerCase();
    let cls = 'bg-secondary';
    if (normalized.includes('baja')) cls = 'bg-danger';
    else if (normalized.includes('asignado') || normalized.includes('usado')) cls = 'bg-primary';
    else if (normalized.includes('disponible') || normalized.includes('activo')) cls = 'bg-success';
    else if (normalized.includes('reparaci')) cls = 'bg-warning';
    return `<span class="badge ${cls}">${value}</span>`;
}

function buildActionButtons(item) {
    const viewUrl = `/asset_profile/view/${item.tipo || 'individual'}/${item.id}`;
    return `
        <a href="${viewUrl}" class="btn btn-sm btn-info" title="Ver Hoja de Vida"><i class="fas fa-eye"></i></a>
        <a href="/inventario/edit/${item.tipo || 'individual'}/${item.id}" class="btn btn-sm btn-warning" title="Editar"><i class="fas fa-edit"></i></a>
        <button class="btn btn-sm btn-success" onclick="openAssignModal('${item.tipo || 'individual'}', ${item.id})" title="Asignar Equipo"><i class="fas fa-user-plus"></i></button>
        <button class="btn btn-sm btn-danger" onclick="deleteItem('${item.tipo || 'individual'}', ${item.id})" title="Eliminar Equipo"><i class="fas fa-trash"></i></button>
    `;
}

function renderSimpleTable(tableId, columns, rows) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let thead = table.querySelector('thead');
    if (!thead) {
        thead = document.createElement('thead');
        table.appendChild(thead);
    }
    thead.innerHTML = `<tr>${columns.map(c => `<th>${c.label}</th>`).join('')}</tr>`;

    let tbody = table.querySelector('tbody');
    if (!tbody) {
        tbody = document.createElement('tbody');
        table.appendChild(tbody);
    }
    tbody.innerHTML = '';

    if (!rows || rows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${columns.length}" class="text-center text-muted">Sin datos para mostrar</td></tr>`;
        return;
    }

    rows.forEach(row => {
        const tr = document.createElement('tr');
        columns.forEach(col => {
            const raw = row[col.key];
            const value = col.formatter ? col.formatter(raw, row) : (raw !== null && raw !== undefined ? raw : '');
            tr.innerHTML += `<td>${value}</td>`;
        });
        tbody.appendChild(tr);
    });
}

async function ensureDashboardData() {
    if (dashboardData) return Promise.resolve(dashboardData);
    try {
        const response = await fetch('/inventarios/api/dashboard');
        if (!response.ok) throw new Error('La respuesta de la red no fue correcta');
        dashboardData = await response.json();
        return dashboardData;
    } catch (error) {
        console.error('Error cargando dashboard de inventarios:', error);
        alert('No se pudo cargar la data del dashboard de inventarios.');
        throw error;
    }
}

function loadGeneralInventory() {
    ensureDashboardData().then(data => {
        renderSimpleTable('generalTable', [
            { key: 'codigo', label: 'Código' },
            { key: 'serial', label: 'Serial' },
            { key: 'marca', label: 'Marca' },
            { key: 'modelo', label: 'Modelo' },
            { key: 'estado', label: 'Estado', formatter: formatEstadoBadge },
            { key: 'asignado', label: 'Asignado a' },
            { key: 'sede', label: 'Sede' },
            { key: 'id', label: 'Acciones', formatter: (id, row) => buildActionButtons(row) }
        ], data.individuales);
    });
}

function loadAssignedInventory() {
    ensureDashboardData().then(data => {
        renderSimpleTable('asignadosTable', [
            { key: 'codigo', label: 'Código' },
            { key: 'marca', label: 'Marca' },
            { key: 'serial', label: 'Serial' },
            { key: 'usuario', label: 'Usuario Asignado' },
            { key: 'sede', label: 'Sede' },
            { key: 'fecha', label: 'Fecha Asignación' },
            { key: 'id', label: 'Acciones', formatter: (id, row) => buildActionButtons(row) }
        ], data.asignados);
    });
}

function loadDecommissionedInventory() {
    ensureDashboardData().then(data => {
        renderSimpleTable('bajasTable', [
            { key: 'codigo', label: 'Código' },
            { key: 'marca', label: 'Marca' },
            { key: 'serial', label: 'Serial' },
            { key: 'motivo', label: 'Motivo de Baja' },
            { key: 'fecha', label: 'Fecha de Baja' }
        ], data.bajas);
    });
}

function loadSedeResumen() {
    ensureDashboardData().then(data => renderSimpleTable('sedeTable', [
        { key: 'sede', label: 'Sede' }, { key: 'total', label: 'Total' }, { key: 'disponibles', label: 'Disponibles' }, { key: 'asignados', label: 'Asignados' }, { key: 'bajas', label: 'Bajas' }
    ], data.por_sede));
}

function loadUsuarioResumen() {
    ensureDashboardData().then(data => renderSimpleTable('usuarioTable', [
        { key: 'usuario', label: 'Usuario' }, { key: 'total', label: 'Total' }, { key: 'activos', label: 'Activos' }, { key: 'bajas', label: 'Bajas' }
    ], data.por_usuario));
}

function loadAreaResumen() {
    ensureDashboardData().then(data => renderSimpleTable('areaTable', [
        { key: 'area', label: 'Área' }, { key: 'total', label: 'Total' }, { key: 'bajas', label: 'Bajas' }
    ], data.por_area));
}

async function deleteItem(table, id) {
    if (!confirm(`¿Estás seguro de que quieres eliminar el ítem con ID ${id} de la tabla ${table}? Esta acción no se puede deshacer.`)) {
        return;
    }

    try {
        const response = await fetch(`/api/delete/${table}/${id}`, {
            method: 'DELETE',
        });

        const result = await response.json();

        if (response.ok && result.success) {
            alert('Ítem eliminado exitosamente.');
            reloadDashboardData(); // Recargar los datos para reflejar el cambio
        } else {
            alert(`Error al eliminar: ${result.error || 'Error desconocido'}`);
        }
    } catch (error) {
        console.error('Error en la petición de eliminación:', error);
        alert('Ocurrió un error de red al intentar eliminar el ítem.');
    }
}

function reloadDashboardData() {
    dashboardData = null;
    const activeTab = document.querySelector('.nav-tabs .nav-link.active');
    if (activeTab) {
        const handler = tabHandlers[activeTab.id];
        if (handler) handler();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const inventoryTabs = document.querySelector('#inventoryTabs');
    if (!inventoryTabs) return;

    // Objeto que mapea el ID de la pestaña con la función que carga sus datos
    const tabHandlers = {
        'general-tab': loadGeneralInventory,
        'asignados-tab': loadAssignedInventory,
        'bajas-tab': loadDecommissionedInventory,
        'por-sede-tab': loadSedeResumen,
        'por-usuario-tab': loadUsuarioResumen,
        'por-area-tab': loadAreaResumen,
    };

    // Escuchar cuando se muestra una nueva pestaña
    inventoryTabs.addEventListener('shown.bs.tab', (event) => {
        const handler = tabHandlers[event.target.id];
        if (handler) {
            handler();
        }
    });

    // Cargar la primera pestaña por defecto
    loadGeneralInventory();
});