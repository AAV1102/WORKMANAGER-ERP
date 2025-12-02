function exportLicencias(type) {
    const table = 'licencias_office365';
    if (['excel', 'pdf', 'csv'].includes(type)) {
        window.location.href = `/export_import/export/${type}/${table}`;
    }
}

function verLicenciasProducto(producto) {
    const detalleTab = document.getElementById('detalle-tab');
    if (detalleTab) detalleTab.click();
    const table = document.getElementById('tablaLicencias');
    if (!table) return;
    const rows = table.querySelectorAll('tbody tr');
    const filterText = (producto || '').toLowerCase();
    rows.forEach(row => {
        const prod = (row.dataset.producto || '').toLowerCase();
        row.style.display = filterText ? (prod.includes(filterText) ? '' : 'none') : '';
    });
    const input = document.getElementById('searchLicencias');
    if (input) input.value = producto || '';
}

function asignarPorSedeProducto(producto) {
    const sedeId = prompt(`Ingresa la sede (ID numérico) para asignar licencias de ${producto}:`);
    if (!sedeId) return;
    const cantidad = prompt('Cantidad de licencias a asignar en esa sede:');
    if (!cantidad || isNaN(cantidad) || Number(cantidad) < 1) {
        alert('Cantidad inválida');
        return;
    }

    fetch('/licencias/api/assign_by_sede', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            sede_id: parseInt(sedeId, 10),
            cantidad: parseInt(cantidad, 10),
            tipo_licencia: producto
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert(data.message || 'Licencias asignadas');
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error assigning by sede:', error);
        alert('Error al asignar licencias por sede');
    });
}

function asignarLicenciaUsuario(email, producto = '', usuarioActual = '', cedula = '') {
    const usuario = prompt('Nombre del usuario asignado', usuarioActual || '');
    if (usuario === null) return;
    const cedulaVal = prompt('Cédula del usuario', cedula || '');
    if (cedulaVal === null) return;
    const sedeId = prompt('Sede (ID numérico)');
    if (sedeId === null || sedeId === '') return;
    const estado = prompt('Estado de la licencia', 'activa') || 'activa';

    fetch('/licencias/api/assign_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email,
            usuario_asignado: usuario,
            cedula_usuario: cedulaVal,
            sede_id: sedeId ? parseInt(sedeId, 10) : null,
            estado,
            tipo_licencia: producto || 'Microsoft 365'
        })
    })
    .then(r => r.json().then(body => ({ ok: r.ok, body })))
    .then(({ ok, body }) => {
        if (!ok) throw new Error(body.error || 'No se pudo asignar la licencia');
        alert(body.message || 'Licencia actualizada');
        window.location.reload();
    })
    .catch(err => {
        console.error(err);
        alert(err.message);
    });
}

function filterBySede() {
    const sedeId = document.getElementById('sedeFilter').value;
    const url = new URL(window.location.href);
    if (sedeId) {
        url.searchParams.set('sede', sedeId);
    } else {
        url.searchParams.delete('sede');
    }
    window.location.href = url.toString();
}

function assignBySede() {
    const sedeId = document.getElementById('assignSede').value;
    const quantity = document.getElementById('assignQuantity').value;
    if (!sedeId || !quantity || Number(quantity) < 1) {
        alert('Por favor selecciona una sede y cantidad válida');
        return;
    }
    fetch('/licencias/api/assign_by_sede', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            sede_id: parseInt(sedeId, 10),
            cantidad: parseInt(quantity, 10)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert(data.message || 'Licencias asignadas');
            window.location.reload();
        }
    })
    .catch(error => {
        console.error('Error assigning by sede:', error);
        alert('Error al asignar licencias por sede');
    });
}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.licencias-detalle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            verLicenciasProducto(btn.dataset.producto || '');
        });
    });

    document.querySelectorAll('.licencias-asignar-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const row = btn.closest('tr');
            const producto = row ? row.dataset.producto : '';
            asignarPorSedeProducto(producto);
        });
    });

    document.querySelectorAll('.licencias-usuario-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const row = btn.closest('tr');
            if (!row) return;
            asignarLicenciaUsuario(
                row.dataset.email || '',
                row.dataset.producto || '',
                row.dataset.usuario || '',
                row.dataset.cedula || ''
            );
        });
    });
});
