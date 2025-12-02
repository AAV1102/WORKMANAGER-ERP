document.addEventListener('DOMContentLoaded', function() {
    const SIDEBAR_BREAKPOINT = 992;
    const wrapper = document.getElementById('wrapper');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    const sidebarToggle = document.getElementById('sidebarToggle');

    const setSidebarOpen = (isOpen) => {
        if (!wrapper) return;
        wrapper.classList.toggle('toggled', !isOpen);
        if (overlay) {
            const shouldShowOverlay = isOpen && window.innerWidth < SIDEBAR_BREAKPOINT;
            overlay.classList.toggle('active', shouldShowOverlay);
        }
    };

    if (sidebarToggle) {
        sidebarToggle.setAttribute('aria-controls', 'sidebar');
        sidebarToggle.addEventListener('click', (event) => {
            event.preventDefault();
            setSidebarOpen(wrapper.classList.contains('toggled'));
        });
    }

    if (overlay) {
        overlay.addEventListener('click', () => setSidebarOpen(false));
    }

    window.addEventListener('resize', () => setSidebarOpen(window.innerWidth >= SIDEBAR_BREAKPOINT));
    setSidebarOpen(window.innerWidth >= SIDEBAR_BREAKPOINT);

    // Inicializar tooltips por compatibilidad
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
