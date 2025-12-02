// JS dedicado al Inventario Maestro
(() => {
  const importBtn = document.getElementById('btnRunImport');
  const importBtnInline = document.getElementById('btnRunImportInline');
  const logBtn = document.getElementById('btnLoadLog');
  const logBox = document.getElementById('importLog');

  function runImport() {
    if (importBtn) importBtn.disabled = true;
    if (importBtnInline) importBtnInline.disabled = true;
    fetch('/inventario-maestro/api/import', { method: 'POST' })
      .then(r => r.json())
      .then(data => {
        alert(data.error || data.message || 'Importador lanzado');
        loadLog();
      })
      .catch(err => alert('Error lanzando importador: ' + err.message))
      .finally(() => {
        if (importBtn) importBtn.disabled = false;
        if (importBtnInline) importBtnInline.disabled = false;
      });
  }

  function loadLog() {
    if (!logBox) return;
    logBox.textContent = 'Cargando log...';
    fetch('/inventario-maestro/api/import/log')
      .then(r => r.json())
      .then(data => {
        logBox.textContent = data.log || 'Sin log.';
      })
      .catch(err => {
        logBox.textContent = 'Error leyendo log: ' + err.message;
      });
  }

  function refreshStats() {
    fetch('/inventario-maestro/api/stats')
      .then(r => r.json())
      .then(stats => {
        document.querySelectorAll('[data-stat="total"]').forEach(el => el.textContent = stats.total_equipos || 0);
        document.querySelectorAll('[data-stat="individuales"]').forEach(el => el.textContent = stats.equipos_individuales || 0);
        document.querySelectorAll('[data-stat="agrupados"]').forEach(el => el.textContent = stats.equipos_agrupados || 0);
        document.querySelectorAll('[data-stat="disponibles"]').forEach(el => el.textContent = stats.equipos_disponibles || 0);
        document.querySelectorAll('[data-stat="asignados"]').forEach(el => el.textContent = stats.equipos_asignados || 0);
        document.querySelectorAll('[data-stat="baja"]').forEach(el => el.textContent = stats.equipos_baja || 0);
      })
      .catch(err => console.error('Error refrescando stats maestro', err));
  }

  document.addEventListener('DOMContentLoaded', () => {
    if (importBtn) importBtn.addEventListener('click', runImport);
    if (importBtnInline) importBtnInline.addEventListener('click', runImport);
    if (logBtn) logBtn.addEventListener('click', loadLog);
    refreshStats();
  });
})();
