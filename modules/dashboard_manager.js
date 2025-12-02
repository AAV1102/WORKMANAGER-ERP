document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('dashboard-container');
    const template = document.getElementById('widget-template');

    // Añadimos el nuevo widget 'inventario_estado' a la lista
    const defaultWidgets = ['empleados', 'inventario', 'licencias', 'inventario_estado', 'tickets'];

    async function loadWidget(widgetName) {
        try {
            const response = await fetch(`/dashboard/widget_data/${widgetName}`);
            if (!response.ok) return;

            const data = await response.json();
            const widgetClone = template.content.cloneNode(true);
            const card = widgetClone.querySelector('.widget-card'); // Usar la clase correcta
            const cardBody = widgetClone.querySelector('.card-body');

            // Limpiar el contenido por defecto del template
            cardBody.innerHTML = ''; 

            // --- Lógica para renderizar diferentes tipos de widgets ---
            if (data.type === 'list' && data.data) {
                // Widget de tipo lista (como el de estados de inventario)
                let listHtml = `<h5 class="card-title"><i class="fas ${data.icon || 'fa-info-circle'} me-2"></i>${data.title}</h5>`;
                listHtml += '<ul class="list-group list-group-flush">';
                data.data.forEach(item => {
                    // Capitalizar el estado para mejor presentación
                    const estado = item.estado ? item.estado.charAt(0).toUpperCase() + item.estado.slice(1) : 'N/A';
                    listHtml += `<li class="list-group-item d-flex justify-content-between align-items-center">${estado}<span class="badge bg-primary rounded-pill">${item.cantidad}</span></li>`;
                });
                listHtml += '</ul>';
                cardBody.innerHTML = listHtml;
                // Quitar clases de alineación que no aplican a listas
                cardBody.classList.remove('d-flex', 'align-items-center');

            } else {
                // Widget KPI estándar (un solo valor)
                const kpiHtml = `
                    <div class="flex-grow-1">
                        <div class="text-xs fw-bold text-primary text-uppercase mb-1 widget-title">${data.title || 'N/A'}</div>
                        <div class="h5 mb-0 fw-bold text-gray-800 widget-value">${data.value}</div>
                        ${data.total ? `<div class="text-xs text-muted">de ${data.total} en total</div>` : ''}
                    </div>
                    <div class="col-auto">
                        <i class="widget-icon fas ${data.icon || 'fa-question-circle'} fa-2x text-gray-300"></i>
                    </div>
                `;
                cardBody.innerHTML = kpiHtml;
            }

            container.appendChild(widgetClone);

        } catch (error) {
            console.error(`Error al cargar el widget ${widgetName}:`, error);
        }
    }

    function loadAllWidgets() {
        container.innerHTML = ''; // Limpiar antes de cargar
        defaultWidgets.forEach(widgetName => {
            loadWidget(widgetName);
        });
    }

    const editButton = document.getElementById('editDashboardBtn');
    if (editButton) {
        editButton.addEventListener('click', () => {
            // Lógica para un modal de personalización (funcionalidad futura)
            alert('Funcionalidad para personalizar el dashboard próximamente. Podrás añadir, quitar y reordenar widgets.');
        });
    }

    // Carga inicial
    loadAllWidgets();
});