(() => {
    const modalEl = document.getElementById('globalModal');
    if (!modalEl) return;

    const modalBody = modalEl.querySelector('#globalModalBody');
    const modalFooter = modalEl.querySelector('#globalModalFooter');
    const modalTitle = modalEl.querySelector('#globalModalLabel');
    const loadingIndicator = modalEl.querySelector('#globalModalLoading');
    const globalModal = new bootstrap.Modal(modalEl);

    function resetModal() {
        if (modalBody) modalBody.innerHTML = loadingIndicator.outerHTML;
        if (modalFooter) {
            const closeBtn = modalFooter.querySelector('[data-bs-dismiss="modal"]');
            modalFooter.innerHTML = '';
            if (closeBtn) modalFooter.appendChild(closeBtn);
        }
    }

    function setBody(html) {
        if (!modalBody) return;
        modalBody.innerHTML = html || '<p class="text-muted">Sin contenido para mostrar.</p>';
    }

    function setFooter(content) {
        if (!modalFooter) return;
        const defaultClose = modalFooter.querySelector('[data-bs-dismiss="modal"]');
        modalFooter.innerHTML = '';
        if (content) {
            modalFooter.insertAdjacentHTML('afterbegin', content);
        }
        if (defaultClose) modalFooter.appendChild(defaultClose);
    }

    function showModal(options = {}) {
        const { title, body, footer } = options;
        if (title && modalTitle) modalTitle.textContent = title;
        setBody(body);
        if (footer !== undefined) {
            setFooter(footer);
        }
        globalModal.show();
    }

    const MODULE_RENDERERS = {
        default: (module, data) => {
            const keys = Object.keys(data || {});
            if (!keys.length) {
                return '<p class="text-muted">No hay detalles adicionales.</p>';
            }
            const list = keys
                .filter(key => key !== 'id')
                .map(key => `<dt class="col-sm-5">${key.replace(/_/g, ' ')}</dt><dd class="col-sm-7">${data[key] ?? ''}</dd>`)
                .join('');
            return `<div class="row"><div class="col-sm-12"><dl class="row">${list}</dl></div></div>`;
        },
        licencia: (module, data) => {
            return `
                <div class="row g-3">
                    <div class="col-md-6">
                        <h5>Licencia</h5>
                        <p><strong>Correo:</strong> ${data.email || 'N/A'}</p>
                        <p><strong>Usuario:</strong> ${data.usuario_asignado || 'N/A'}</p>
                        <p><strong>Estado:</strong> ${data.estado || 'N/A'}</p>
                    </div>
                    <div class="col-md-6">
                        <h5>Producto</h5>
                        <p><strong>Tipo:</strong> ${data.tipo_licencia || 'Microsoft 365'}</p>
                        <p><strong>Asignada:</strong> ${data.fecha_asignacion || 'N/D'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p class="text-muted">${data.observaciones || 'Sin observaciones'}</p>
                </div>
            `;
        },
        empleado: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <h5>Empleado</h5>
                        <p><strong>Nombre:</strong> ${data.nombre || ''} ${data.apellido || ''}</p>
                        <p><strong>Cédula:</strong> ${data.cedula || 'N/A'}</p>
                        <p><strong>Cargo:</strong> ${data.cargo || 'N/A'}</p>
                        <p><strong>Sede:</strong> ${data.sede_nombre || 'Sin sede'}</p>
                    </div>
                    <div class="col-md-6">
                        <h5>Contacto</h5>
                        <p><strong>Correo:</strong> ${data.correo_office || 'N/A'}</p>
                        <p><strong>Usuario Windows:</strong> ${data.usuario_windows || 'N/A'}</p>
                        <p><strong>Quirón:</strong> ${data.usuario_quiron || 'N/A'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p><strong>Observaciones:</strong> ${data.observaciones || 'Sin observaciones'}</p>
                </div>
            `;
        },
        inventario_individual: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Código:</strong> ${data.codigo_barras_individual || data.id}</p>
                        <p><strong>Serial:</strong> ${data.serial || 'N/D'}</p>
                        <p><strong>Marca/Modelo:</strong> ${data.marca || 'N/D'} ${data.modelo || ''}</p>
                        <p><strong>Tecnología:</strong> ${data.tecnologia || 'N/D'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Sede:</strong> ${data.sede_nombre || data.sede || 'Sin sede'}</p>
                        <p><strong>Asignado:</strong> ${data.asignado_nuevo || data.asignado_a || 'Sin asignación'}</p>
                        <p><strong>Estado:</strong> ${data.estado || 'N/D'}</p>
                        <p><strong>Fecha llegada:</strong> ${data.fecha_llegada || data.fecha || 'N/D'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p>${data.observaciones || 'Sin observaciones'}</p>
                </div>
            `;
        },
        inventario_agrupado: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Código unificado:</strong> ${data.codigo_barras_unificado || data.id}</p>
                        <p><strong>Descripción:</strong> ${data.descripcion_general || 'Sin descripción'}</p>
                        <p><strong>Estado:</strong> ${data.estado_general || 'N/D'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Sede:</strong> ${data.sede_nombre || 'Sin sede'}</p>
                        <p><strong>Asignado actual:</strong> ${data.asignado_actual || 'Sin asignación'}</p>
                        <p><strong>Creado:</strong> ${data.fecha_creacion || 'N/D'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p>${data.observaciones || 'Sin observaciones'}</p>
                </div>
            `;
        },
        asignacion: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Destino:</strong> ${data.nombre_destino || 'N/D'}</p>
                        <p><strong>Ciudad:</strong> ${data.ciudad_destino || 'N/D'}</p>
                        <p><strong>Fecha envío:</strong> ${data.fecha_envio || 'N/D'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Equipo:</strong> ${data.codigo_equipo || 'Sin equipo asociado'}</p>
                        <p><strong>Marca/Modelo:</strong> ${data.marca || ''} ${data.modelo || ''}</p>
                        <p><strong>Serial:</strong> ${data.serial || 'N/D'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p>${data.observaciones || 'Sin observaciones'}</p>
                </div>
            `;
        },
        compra: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Entidad:</strong> ${data.entidad || 'N/D'}</p>
                        <p><strong>Artículo:</strong> ${data.articulo || 'N/D'}</p>
                        <p><strong>Fecha:</strong> ${data.fecha || 'N/D'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>NIT:</strong> ${data.nit || 'N/D'}</p>
                        <p><strong>Ciudad:</strong> ${data.ciudad || 'N/D'}</p>
                        <p><strong>Cantidad:</strong> ${data.cantidad || 0}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p><strong>Equipo vinculado:</strong> ${data.codigo_equipo || 'Sin relación'}</p>
                    <p>${data.serial_equipo || ''}</p>
                </div>
            `;
        },
        mantenimiento: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Título:</strong> ${data.titulo || 'N/D'}</p>
                        <p><strong>Equipo ID:</strong> ${data.equipo_id || 'N/D'}</p>
                        <p><strong>Tipo:</strong> ${data.tipo_equipo || 'N/D'}</p>
                        <p><strong>Responsable:</strong> ${data.responsable || 'N/D'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Estado:</strong> ${data.estado || 'N/D'}</p>
                        <p><strong>Fecha programada:</strong> ${data.fecha_programada || 'N/D'}</p>
                        <p><strong>Costo:</strong> ${data.costo || 'N/D'}</p>
                        <p><strong>Creado:</strong> ${data.created_at || 'N/D'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p>${data.descripcion || 'Sin descripción'}</p>
                </div>
            `;
        },
        infraestructura_administrativa: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Tipo:</strong> ${data.tipo_mueble || 'N/D'}</p>
                        <p><strong>Código:</strong> ${data.codigo_interno || 'N/D'}</p>
                        <p><strong>Estado:</strong> ${data.estado || 'N/D'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Asignado a:</strong> ${data.asignado_a || 'Sin asignar'}</p>
                        <p><strong>Ubicación:</strong> ${data.area_recibe || 'N/D'}</p>
                        <p><strong>Cantidad:</strong> ${data.cantidad || 1}</p>
                        <p><strong>Fecha compra:</strong> ${data.fecha_compra || 'N/D'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p>${data.descripcion_item || 'Sin descripción'}</p>
                </div>
            `;
        },
        insumo: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Nombre:</strong> ${data.nombre_insumo || 'N/D'}</p>
                        <p><strong>Serial:</strong> ${data.serial_equipo || 'N/D'}</p>
                        <p><strong>Ubicación:</strong> ${data.ubicacion || 'N/D'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Total:</strong> ${data.cantidad_total || 0}</p>
                        <p><strong>Disponibles:</strong> ${data.cantidad_disponible || 0}</p>
                        <p><strong>Estado:</strong> ${data.estado || 'N/D'}</p>
                        <p><strong>Asignado a:</strong> ${data.asignado_a || 'Sin asignación'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p>${data.observaciones || 'Sin observaciones'}</p>
                </div>
            `;
        },
        factura: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Número:</strong> ${data.numero_factura || 'N/D'}</p>
                        <p><strong>Proveedor:</strong> ${data.nombre_proveedor || 'N/D'}</p>
                        <p><strong>Tipo:</strong> ${data.tipo_factura || 'N/D'}</p>
                        <p><strong>Fecha:</strong> ${data.fecha_factura || 'N/D'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Total:</strong> $${Number(data.valor_factura || 0).toLocaleString()}</p>
                        <p><strong>Autorizado por:</strong> ${data.autorizado_por || 'N/D'}</p>
                        <p><strong>Estado:</strong> ${data.estado || 'N/D'}</p>
                        <p><strong>Documentos:</strong> ${data.documentos_soporte || 'N/A'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p>${data.observaciones || 'Sin observaciones'}</p>
                </div>
            `;
        },
        garantia: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Equipo:</strong> ${data.nombre_equipo || data.descripcion_general || 'N/D'}</p>
                        <p><strong>Serial:</strong> ${data.serial || 'N/D'}</p>
                        <p><strong>Proveedor:</strong> ${data.proveedor || 'N/D'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Estado:</strong> ${data.estado_general || 'N/D'}</p>
                        <p><strong>Fin garantía:</strong> ${data.fecha_fin_garantia || 'N/D'}</p>
                        <p><strong>Días restantes:</strong> ${data.dias_restantes || 'N/D'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p>${data.observaciones || 'Sin observaciones'}</p>
                </div>
            `;
        },
        inventario_administrativo: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Tipo:</strong> ${data.tipo_mueble || 'N/D'}</p>
                        <p><strong>Código interno:</strong> ${data.codigo_interno || 'N/D'}</p>
                        <p><strong>Descripción:</strong> ${data.descripcion_item || 'Sin descripción'}</p>
                        <p><strong>Estado:</strong> ${data.estado || 'N/D'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Asignado a:</strong> ${data.asignado_a || 'Sin asignar'}</p>
                        <p><strong>Área:</strong> ${data.area_recibe || 'N/D'}</p>
                        <p><strong>Fecha compra:</strong> ${data.fecha_compra || 'N/D'}</p>
                        <p><strong>Cantidad:</strong> ${data.cantidad || 1}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p>${data.observaciones || 'Sin observaciones'}</p>
                </div>
            `;
        },

        alerta: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Nivel:</strong> ${data.nivel || data.level || 'info'}</p>
                        <p><strong>Origen:</strong> ${data.origen || data.source || 'Sistema'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Tipo:</strong> ${data.tipo || data.alert_type || 'General'}</p>
                        <p><strong>Fecha:</strong> ${data.fecha || data.created_at || data.timestamp || 'N/D'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p>${data.mensaje || data.descripcion || data.body || 'Sin descripción'}</p>
                </div>
            `;
        },
        solicitud: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Tipo:</strong> ${data.tipo || 'General'}</p>
                        <p><strong>Estado:</strong> ${data.estado || 'pendiente'}</p>
                        <p><strong>Solicitante:</strong> ${data.empleado_id || data.usuario || 'N/D'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Fecha solicitud:</strong> ${data.fecha_solicitud || 'N/D'}</p>
                        <p><strong>Fecha aprobación:</strong> ${data.fecha_aprobacion || 'No aprobada'}</p>
                        <p><strong>Motivo rechazo:</strong> ${data.motivo_rechazo || '-'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p>${data.descripcion || 'Sin descripción'}</p>
                </div>
            `;
        },
        reporte: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Tipo de reporte:</strong> ${data.tipo_reporte || 'RRHH'}</p>
                        <p><strong>Período:</strong> ${data.periodo || 'N/D'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Generado por:</strong> ${data.generado_por || 'N/D'}</p>
                        <p><strong>Fecha generación:</strong> ${data.fecha_generacion || 'N/D'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p>${data.datos || data.descripcion || 'Sin información adicional'}</p>
                </div>
            `;
        },
        sede: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Nombre:</strong> ${data.nombre || 'Sede sin nombre'}</p>
                        <p><strong>Ciudad:</strong> ${data.ciudad || 'N/D'}</p>
                        <p><strong>Departamento:</strong> ${data.departamento || 'N/D'}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Dirección:</strong> ${data.direccion || 'Sin dirección'}</p>
                        <p><strong>Teléfono:</strong> ${data.telefono || 'N/D'}</p>
                        <p><strong>Contacto:</strong> ${data.contacto || '-'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p>${data.observaciones || 'Sin observaciones'}</p>
                </div>
            `;
        },
        ticket: (module, data) => {
            return `
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Título:</strong> ${data.titulo || data.title}</p>
                        <p><strong>Categoría:</strong> ${data.categoria || data.category}</p>
                        <p><strong>Prioridad:</strong> ${data.prioridad || data.priority}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Estado:</strong> ${data.estado || data.status}</p>
                        <p><strong>Reporta:</strong> ${data.usuario_reporta_id || 'N/A'}</p>
                        <p><strong>Asignado:</strong> ${data.usuario_asignado_id || 'Sin encargado'}</p>
                    </div>
                </div>
                <div class="mt-3">
                    <p>${data.descripcion || 'Sin descripción'}</p>
                </div>
            `;
        }
    };

    function loadRemote(url, title) {
        resetModal();
        if (title && modalTitle) modalTitle.textContent = title;
        fetch(url, { credentials: 'same-origin' })
            .then(response => response.text())
            .then(html => {
                setBody(html);
                globalModal.show();
            })
            .catch(err => {
                setBody(`<div class="alert alert-danger">Error al cargar el contenido: ${err.message}</div>`);
                globalModal.show();
            });
    }

    function loadApi(url, title, rendererName, trigger) {
        resetModal();
        if (title && modalTitle) modalTitle.textContent = title;
        fetch(url, { credentials: 'same-origin' })
            .then(response => response.json())
            .then(payload => {
                if (payload.error) {
                    setBody(`<div class="alert alert-warning">${payload.error}</div>`);
                } else {
                    const renderer = MODULE_RENDERERS[rendererName] || MODULE_RENDERERS[payload.data?.module] || MODULE_RENDERERS.default;
                    setBody(renderer(payload.module || rendererName, payload.data || {}));
                }
                globalModal.show();
            })
            .catch(err => {
                setBody(`<div class="alert alert-danger">Error al cargar el contenido: ${err.message}</div>`);
                globalModal.show();
            });
    }

    document.addEventListener('click', (event) => {
        const trigger = event.target.closest('[data-modal-url], [data-modal-api]');
        if (!trigger) return;
        event.preventDefault();
        const apiUrl = trigger.dataset.modalApi;
        const url = trigger.dataset.modalUrl;
        const title = trigger.dataset.modalTitle || 'Detalle';
        const footer = trigger.dataset.modalFooter;
        const renderer = trigger.dataset.modalRenderer;
        if (apiUrl) {
            loadApi(apiUrl, title, renderer, trigger);
        } else if (url) {
            loadRemote(url, title);
        } else {
            const body = trigger.dataset.modalBody || '';
            showModal({ title, body, footer });
        }
    });

    window.openGlobalModal = showModal;
    window.openRemoteModal = (url, title) => loadRemote(url, title);
    window.openApiModal = (url, title, renderer) => loadApi(url, title, renderer);
})();
