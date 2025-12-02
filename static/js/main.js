// WORKMANAGER ERP - Funciones de Búsqueda y Filtrado

/**
 * Redirige la página actual aplicando un filtro desde un campo select.
 * @param {string} selectId - El ID del elemento <select> que contiene el valor del filtro.
 * @param {string} paramName - El nombre del parámetro que se añadirá a la URL (ej: 'sede', 'estado').
 */
function filterBySelect(selectId, paramName) {
    const selectElement = document.getElementById(selectId);
    if (!selectElement) {
        console.error(`Elemento con ID '${selectId}' no encontrado.`);
        return;
    }
    const filterValue = selectElement.value;
    const url = new URL(window.location.href);

    if (filterValue) {
        url.searchParams.set(paramName, filterValue);
    } else {
        url.searchParams.delete(paramName);
    }
    window.location.href = url.toString();
}

/**
 * Redirige la página actual aplicando un término de búsqueda desde un campo de texto.
 * @param {string} inputId - El ID del elemento <input> que contiene el término de búsqueda.
 * @param {string} paramName - El nombre del parámetro de búsqueda (ej: 'q', 'search').
 */
function searchByInput(inputId, paramName = 'q') {
    const inputElement = document.getElementById(inputId);
    const query = inputElement.value;
    const url = new URL(window.location.href);
    url.searchParams.set(paramName, query);
    window.location.href = url.toString();
}

// WORKMANAGER ERP - Main JavaScript Functions

// Global functions for all modules

// Search functionality
function searchTable(tableId, searchInputId) {
    const input = document.getElementById(searchInputId);
    const filter = input.value.toUpperCase();
    const table = document.getElementById(tableId);
    const tr = table.getElementsByTagName('tr');

    for (let i = 1; i < tr.length; i++) {
        const td = tr[i].getElementsByTagName('td');
        let found = false;
        for (let j = 0; j < td.length; j++) {
            if (td[j]) {
                const textValue = td[j].textContent || td[j].innerText;
                if (textValue.toUpperCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }
        }
        tr[i].style.display = found ? '' : 'none';
    }
}

// Filter by status
function filterByStatus(tableId, status) {
    const table = document.getElementById(tableId);
    const tr = table.getElementsByTagName('tr');

    for (let i = 1; i < tr.length; i++) {
        const td = tr[i].getElementsByTagName('td');
        let show = false;

        if (status === 'all') {
            show = true;
        } else {
            for (let j = 0; j < td.length; j++) {
                if (td[j]) {
                    const badge = td[j].querySelector('.badge');
                    if (badge && badge.textContent.toLowerCase() === status.toLowerCase()) {
                        show = true;
                        break;
                    }
                }
            }
        }
        tr[i].style.display = show ? '' : 'none';
    }
}

// Confirm delete action
function confirmDelete(message = '¿Estás seguro de que quieres eliminar este elemento?') {
    return confirm(message);
}

// Show loading spinner
function showLoading(buttonId) {
    const button = document.getElementById(buttonId);
    if (button) {
        button.disabled = true;
        button.innerHTML = '<span class="loading"></span> Procesando...';
    }
}

// Hide loading spinner
function hideLoading(buttonId, originalText) {
    const button = document.getElementById(buttonId);
    if (button) {
        button.disabled = false;
        button.innerHTML = originalText;
    }
}

// Export data function
function exportData(type, table) {
    const url = `/export_import/export/${type}/${table}`;
    window.open(url, '_blank');
}

// Import data function
function importData(table) {
    if (!table) {
        table = window.location.pathname.split('/')[1] || 'inventarios';
    }
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.xlsx,.xls,.csv';
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (file) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('table', table);

            showLoading('importBtn');

            fetch(`/export_import/import/excel/${table}`, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                hideLoading('importBtn', 'Importar Datos');
                if (data.message) {
                    alert('Importación exitosa: ' + data.message);
                    location.reload();
                } else {
                    alert('Error en la importación: ' + data.error);
                }
            })
            .catch(error => {
                hideLoading('importBtn', 'Importar Datos');
                alert('Error en la importación: ' + error.message);
            });
        }
    };
    input.click();
}

// Generate barcode
function generateBarcode(itemId) {
    if (!itemId) {
        itemId = prompt('Ingrese el ID del equipo para generar código de barras:');
    }
    if (itemId) {
        window.open(`/export_import/export/barcode/${itemId}`, '_blank');
    }
}

// Generate life sheet
function generateLifeSheet(itemId) {
    if (!itemId) {
        itemId = prompt('Ingrese el ID del equipo para generar hoja de vida:');
    }
    if (itemId) {
        window.open(`/export_import/export/life_sheet/${itemId}`, '_blank');
    }
}

// Save data notification
function saveData() {
    // Show success message
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed';
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        <strong>¡Éxito!</strong> Datos guardados correctamente.
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);

    // Auto remove after 3 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Auto-save functionality (optional)
let autoSaveTimer;
function enableAutoSave(formId, interval = 30000) { // 30 seconds default
    const form = document.getElementById(formId);
    if (form) {
        form.addEventListener('input', function() {
            clearTimeout(autoSaveTimer);
            autoSaveTimer = setTimeout(() => {
                // Auto-save logic here
                console.log('Auto-saving...');
            }, interval);
        });
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl+S to save
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        saveData();
    }

    // Ctrl+F to focus search
    if (e.ctrlKey && e.key === 'f') {
        e.preventDefault();
        const searchInput = document.querySelector('input[type="search"], input[placeholder*="Buscar"], input[placeholder*="Search"]');
        if (searchInput) {
            searchInput.focus();
        }
    }

    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    }
});

// Print functionality
function printTable(tableId) {
    const table = document.getElementById(tableId);
    if (table) {
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
                <head>
                    <title>WORKMANAGER ERP - Reporte</title>
                    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                    <style>
                        body { padding: 20px; }
                        .no-print { display: none; }
                    </style>
                </head>
                <body>
                    <h2 class="text-center mb-4">WORKMANAGER ERP - Reporte</h2>
                    ${table.outerHTML}
                    <div class="text-center mt-4 no-print">
                        <button onclick="window.print()" class="btn btn-primary">Imprimir</button>
                        <button onclick="window.close()" class="btn btn-secondary">Cerrar</button>
                    </div>
                </body>
            </html>
        `);
        printWindow.document.close();
    }
}

// Date formatting
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

// Number formatting
function formatNumber(number) {
    return new Intl.NumberFormat('es-ES').format(number);
}

// Currency formatting
function formatCurrency(amount, currency = 'COP') {
    return new Intl.NumberFormat('es-ES', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

// Notification system
function showNotification(message, type = 'info', duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);

    // Auto remove
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, duration);
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    showNotification('Ha ocurrido un error inesperado. Por favor, recarga la página.', 'danger');
});

// Unhandled promise rejections
window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e.reason);
    showNotification('Ha ocurrido un error en la aplicación.', 'danger');
});

/**
 * Exports data from a table, including current client-side filters.
 * @param {string} format - The export format (e.g., 'excel', 'pdf').
 * @param {string} tableId - The ID of the table to export from.
 * @param {string} searchInputId - The ID of the search input field.
 * @param {string} exportUrl - The base URL for the export endpoint.
 */
function exportFilteredData(format, tableId, searchInputId, exportUrl) {
    const searchInput = document.getElementById(searchInputId);
    const table = document.getElementById(tableId);

    const params = new URLSearchParams();

    // 1. Add search query
    if (searchInput && searchInput.value) {
        params.append('q', searchInput.value);
    }

    // 2. Add sorting info
    if (table) {
        const sortedHeader = table.querySelector('th[data-sort-dir]');
        if (sortedHeader) {
            const colIndex = Array.from(sortedHeader.parentNode.children).indexOf(sortedHeader);
            const colName = sortedHeader.dataset.sortKey || sortedHeader.textContent.trim().toLowerCase().replace(/\s+/g, '_');
            params.append('sort_by', colName);
            params.append('sort_dir', sortedHeader.dataset.sortDir);
        }
    }

    // 3. Build and navigate to the final URL
    window.location.href = `${exportUrl}/${format}?${params.toString()}`;
}

// Export/Import modal functions
let currentExportType = '';

const TABLE_GUESS = {
    agrupados: 'equipos_agrupados',
    individuales: 'equipos_individuales',
    asignados: 'equipos_individuales',
    bajas: 'inventario_bajas'
};

function getCurrentTable() {
    const path = window.location.pathname;

    // Inventarios tabs
    if (path.includes('inventarios')) {
        const activeTab = document.querySelector('#inventoryTabs .nav-link.active');
        const target = activeTab ? activeTab.getAttribute('data-bs-target') : '';
        if (target === '#agrupados') return 'equipos_agrupados';
        if (target === '#bajas') return 'inventario_bajas';
        // individuales, asignados, general -> individuales
        return 'equipos_individuales';
    }

    if (path.includes('licencias')) return 'licencias_office365';
    if (path.includes('proveedores')) return 'proveedores';
    if (path.includes('empleados') || path.includes('gestion-humana')) return 'empleados';

    // Default fallback
    return 'equipos_individuales';
}

function showExportModal(type) {
    currentExportType = type;
    const table = getCurrentTable();

    // Fetch table columns
    fetch(`/export_import/get_columns/${table}`)
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('columnsContainer');
            container.innerHTML = '';

            if (data.columns && data.columns.length > 0) {
                const selectAllDiv = document.createElement('div');
                selectAllDiv.className = 'mb-3';
                selectAllDiv.innerHTML = `
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="selectAllColumns" checked>
                        <label class="form-check-label" for="selectAllColumns">
                            <strong>Seleccionar todas las columnas</strong>
                        </label>
                    </div>
                `;
                container.appendChild(selectAllDiv);

                const columnsDiv = document.createElement('div');
                columnsDiv.className = 'row g-2 mb-3';
                const heading = document.createElement('h6');
                heading.textContent = 'Seleccionar columnas específicas:';
                container.appendChild(heading);

                data.columns.forEach(column => {
                    const labelText = column.replace(/_/g, ' ');
                    const colDiv = document.createElement('div');
                    colDiv.className = 'col-6 col-md-4';
                    colDiv.innerHTML = `
                        <div class="form-check">
                            <input class="form-check-input column-checkbox" type="checkbox" id="col_${column}" value="${column}" checked>
                            <label class="form-check-label" for="col_${column}">
                                ${labelText}
                            </label>
                        </div>
                    `;
                    columnsDiv.appendChild(colDiv);
                });

                container.appendChild(columnsDiv);

                // Handle select all functionality
                document.getElementById('selectAllColumns').addEventListener('change', function() {
                    const checkboxes = document.querySelectorAll('.column-checkbox');
                    checkboxes.forEach(cb => cb.checked = this.checked);
                });
            }

            const modal = new bootstrap.Modal(document.getElementById('exportModal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error fetching columns:', error);
            // Fallback to direct export
            performExport();
        });
}

function performExport() {
    const table = getCurrentTable();
    const selectedColumns = Array.from(document.querySelectorAll('.column-checkbox:checked')).map(cb => cb.value);

    let url = `/export_import/export/${currentExportType}/${table}`;
    if (selectedColumns.length > 0) {
        url += `?columns=${selectedColumns.join(',')}`;
    }

    window.location.href = url;

    const modal = bootstrap.Modal.getInstance(document.getElementById('exportModal'));
    if (modal) modal.hide();
}

// ====== Export/Import overrides with presets and barcode prompt ======
// Presets de columnas por tabla para mostrar opciones legibles
const COLUMN_PRESETS = {
    equipos_individuales: [
        { key: 'id', label: 'ID' },
        { key: 'codigo_barras_individual', label: 'Codigo Individual' },
        { key: 'codigo_unificado', label: 'Codigo Unificado' },
        { key: 'serial', label: 'Serial' },
        { key: 'placa', label: 'Placa' },
        { key: 'anterior_placa', label: 'Anterior Placa' },
        { key: 'sede_id', label: 'Sede ID' },
        { key: 'tecnologia', label: 'Tecnologia' },
        { key: 'marca', label: 'Marca' },
        { key: 'modelo', label: 'Modelo' },
        { key: 'estado', label: 'Estado' },
        { key: 'asignado_nuevo', label: 'Asignado A' },
        { key: 'fecha_asignacion', label: 'Fecha Asignacion' },
        { key: 'observaciones', label: 'Observaciones' },
        { key: 'mouse', label: 'Mouse' },
        { key: 'teclado', label: 'Teclado' }
    ],
    equipos_agrupados: [
        { key: 'id', label: 'ID' },
        { key: 'codigo_barras_unificado', label: 'Codigo Unificado' },
        { key: 'descripcion_general', label: 'Descripcion' },
        { key: 'asignado_actual', label: 'Asignado A' },
        { key: 'sede_id', label: 'Sede ID' },
        { key: 'estado_general', label: 'Estado' },
        { key: 'creador_registro', label: 'Creador' },
        { key: 'fecha_creacion', label: 'Fecha Creacion' }
    ],
    inventario_bajas: [
        { key: 'id', label: 'ID' },
        { key: 'equipo_id', label: 'Equipo ID' },
        { key: 'tipo_inventario', label: 'Tipo Inventario' },
        { key: 'motivo_baja', label: 'Motivo' },
        { key: 'fecha_baja', label: 'Fecha Baja' },
        { key: 'responsable_baja', label: 'Responsable' }
    ],
    licencias_office365: [
        { key: 'id', label: 'ID' },
        { key: 'email', label: 'Email' },
        { key: 'tipo_licencia', label: 'Tipo Licencia' },
        { key: 'usuario_asignado', label: 'Usuario' },
        { key: 'estado', label: 'Estado' },
        { key: 'sede_id', label: 'Sede ID' },
        { key: 'fecha_asignacion', label: 'Fecha Asignacion' }
    ],
    proveedores: [
        { key: 'id', label: 'ID' },
        { key: 'nit', label: 'NIT' },
        { key: 'nombre', label: 'Nombre' },
        { key: 'tipo_persona', label: 'Tipo Persona' },
        { key: 'email', label: 'Email' },
        { key: 'telefono', label: 'Telefono' },
        { key: 'ciudad', label: 'Ciudad' },
        { key: 'estado', label: 'Estado' }
    ],
    empleados: [
        { key: 'id', label: 'ID' },
        { key: 'cedula', label: 'Cedula' },
        { key: 'nombre', label: 'Nombre' },
        { key: 'apellido', label: 'Apellido' },
        { key: 'cargo', label: 'Cargo' },
        { key: 'departamento', label: 'Departamento' },
        { key: 'sede_id', label: 'Sede ID' },
        { key: 'estado', label: 'Estado' }
    ]
};

// Reemplazo de showExportModal/performExport con presets y barcode prompt
function showExportModal(type) {
    currentExportType = type;
    if (type === 'barcode') {
        showBarcodePrompt();
        return;
    }
    const table = getCurrentTable();
    const preset = COLUMN_PRESETS[table];

    const container = document.getElementById('columnsContainer');
    container.innerHTML = '';

    const selectAllDiv = document.createElement('div');
    selectAllDiv.className = 'mb-3';
    selectAllDiv.innerHTML = `
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="selectAllColumns" checked>
            <label class="form-check-label" for="selectAllColumns">
                <strong>Seleccionar todas las columnas</strong>
            </label>
        </div>
    `;
    container.appendChild(selectAllDiv);

    const columnsDiv = document.createElement('div');
    columnsDiv.className = 'row g-2 mb-3';
    const heading = document.createElement('h6');
    heading.textContent = 'Seleccionar columnas específicas:';
    container.appendChild(heading);

    const renderColumns = cols => {
        cols.forEach(col => {
            const key = typeof col === 'string' ? col : col.key;
            const label = typeof col === 'string' ? col.replace(/_/g, ' ') : col.label;
            const colDiv = document.createElement('div');
            colDiv.className = 'col-6 col-md-4';
            colDiv.innerHTML = `
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col_${key}" value="${key}" checked>
                    <label class="form-check-label" for="col_${key}">
                        ${label}
                    </label>
                </div>
            `;
            columnsDiv.appendChild(colDiv);
        });
    };

    if (preset && preset.length) {
        renderColumns(preset);
    } else {
        fetch(`/export_import/get_columns/${table}`)
            .then(response => response.json())
            .then(data => {
                renderColumns(data.columns || []);
            })
            .catch(() => {});
    }

    container.appendChild(columnsDiv);

    document.getElementById('selectAllColumns').addEventListener('change', function() {
        const checkboxes = document.querySelectorAll('.column-checkbox');
        checkboxes.forEach(cb => cb.checked = this.checked);
    });

    const modal = new bootstrap.Modal(document.getElementById('exportModal'));
    modal.show();
}

function performExport() {
    const table = getCurrentTable();
    if (currentExportType === 'barcode') {
        showBarcodePrompt();
        return;
    }
    const selectedColumns = Array.from(document.querySelectorAll('.column-checkbox:checked')).map(cb => cb.value);

    let url = `/export_import/export/${currentExportType}/${table}`;
    if (selectedColumns.length > 0) {
        url += `?columns=${selectedColumns.join(',')}`;
    }

    window.location.href = url;

    const modal = bootstrap.Modal.getInstance(document.getElementById('exportModal'));
    if (modal) modal.hide();
}

function showBarcodePrompt() {
    const code = prompt('Ingrese el codigo o ID para generar codigo de barras (agrupado/individual/sede):');
    if (!code) return;
    window.location.href = `/export_import/export/barcode/${encodeURIComponent(code)}`;
}

function showImportModal() {
    const modal = new bootstrap.Modal(document.getElementById('importModal'));
    modal.show();
}

function performImport() {
    const fileInput = document.getElementById('importFile');
    const tableSelect = document.getElementById('importTable');

    if (!fileInput.files[0]) {
        alert('Por favor seleccione un archivo');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    const table = tableSelect.value;

    showLoading('performImportBtn');

    fetch(`/export_import/import/excel/${table}`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        hideLoading('performImportBtn', 'Importar');
        if (data.message) {
            alert('Importación exitosa: ' + data.message);
            location.reload();
        } else {
            alert('Error en la importación: ' + data.error);
        }

        const modal = bootstrap.Modal.getInstance(document.getElementById('importModal'));
        if (modal) modal.hide();
    })
    .catch(error => {
        hideLoading('performImportBtn', 'Importar');
        alert('Error en la importación: ' + error.message);
    });
}
