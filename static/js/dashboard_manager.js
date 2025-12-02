document.addEventListener('DOMContentLoaded', function () {
    const dashboardContainer = document.getElementById('dashboard-container');
    // Lista de widgets a mostrar. En el futuro, esto vendrá de la configuración del usuario.
    const widgets = ['empleados', 'inventario', 'licencias', 'tickets', 'inventario_estado'];

    if (!dashboardContainer) return;

    // Inicializar tooltips de Bootstrap para el botón "Personalizar"
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Función para renderizar un widget de tipo KPI (Key Performance Indicator)
    function renderKpiWidget(widget) {
        return `
            <div class="col-lg-3 col-md-6 mb-4">
                <div class="card border-left-primary shadow-sm h-100 py-2">
                    <div class="card-body">
                        <div class="row no-gutters align-items-center">
                            <div class="col mr-2">
                                <div class="text-xs font-weight-bold text-primary text-uppercase mb-1">${widget.title}</div>
                                <div class="h5 mb-0 font-weight-bold text-gray-800">${widget.value} / ${widget.total}</div>
                            </div>
                            <div class="col-auto">
                                <i class="fas ${widget.icon} fa-2x text-gray-300"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Función para renderizar un widget de tipo lista
    function renderListWidget(widget) {
        let listItems = '';
        if (widget.data && widget.data.length > 0) {
            listItems = widget.data.map(item => `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    ${item.estado}
                    <span class="badge bg-primary rounded-pill">${item.cantidad}</span>
                </li>
            `).join('');
        } else {
            listItems = '<li class="list-group-item text-muted">No hay datos.</li>';
        }

        return `
            <div class="col-lg-3 col-md-6 mb-4">
                <div class="card shadow-sm h-100">
                    <div class="card-header py-3">
                        <h6 class="m-0 font-weight-bold text-primary"><i class="fas ${widget.icon} me-2"></i>${widget.title}</h6>
                    </div>
                    <div class="card-body p-0">
                        <ul class="list-group list-group-flush">
                            ${listItems}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }

    // Cargar los datos de todos los widgets
    async function loadWidgets() {
        dashboardContainer.innerHTML = '<p class="text-muted">Cargando datos del dashboard...</p>';
        let content = '';

        for (const widgetName of widgets) {
            try {
                const response = await fetch(`/dashboard/widget_data/${widgetName}`);
                const widgetData = await response.json();

                if (widgetData.type === 'list') {
                    content += renderListWidget(widgetData);
                } else {
                    content += renderKpiWidget(widgetData);
                }
            } catch (error) {
                console.error(`Error al cargar el widget ${widgetName}:`, error);
            }
        }
        dashboardContainer.innerHTML = content;
    }

    loadWidgets();
});