document.addEventListener('DOMContentLoaded', () => {
    const notificationsCount = document.getElementById('notifications-count');
    const notificationsList = document.getElementById('notifications-list');
    const notificationsDropdown = document.getElementById('notificationsDropdown');

    async function fetchNotifications() {
        try {
            const response = await fetch('/notifications/api/unread');
            if (!response.ok) return;

            const data = await response.json();
            updateNotificationsUI(data);
        } catch (error) {
            console.error('Error fetching notifications:', error);
        }
    }

    function updateNotificationsUI(data) {
        // Actualizar contador
        if (data.count > 0) {
            notificationsCount.textContent = data.count;
            notificationsCount.style.display = 'block';
        } else {
            notificationsCount.style.display = 'none';
        }

        // Limpiar y llenar la lista
        notificationsList.innerHTML = '';
        if (data.notifications.length > 0) {
            data.notifications.forEach(n => {
                const li = document.createElement('li');
                const a = document.createElement('a');
                a.classList.add('dropdown-item', 'text-wrap');
                a.href = n.url || '#';
                a.dataset.id = n.id;
                a.innerHTML = `<div class="fw-bold">${n.message}</div><div class="small text-muted">${new Date(n.created_at).toLocaleString()}</div>`;
                li.appendChild(a);
                notificationsList.appendChild(li);
            });
            notificationsList.innerHTML += '<li><hr class="dropdown-divider"></li>';
            notificationsList.innerHTML += '<li><a class="dropdown-item text-center" href="#" id="mark-all-read-btn">Marcar todo como leído</a></li>';
        } else {
            notificationsList.innerHTML = '<li><span class="dropdown-item text-muted">No hay notificaciones nuevas</span></li>';
        }
    }

    async function markAsRead(ids = []) {
        try {
            await fetch('/notifications/api/mark_as_read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ids: ids }),
            });
            // Refrescar inmediatamente después de marcar como leído
            fetchNotifications();
        } catch (error) {
            console.error('Error marking notifications as read:', error);
        }
    }

    // Evento para marcar todo como leído
    notificationsList.addEventListener('click', (e) => {
        if (e.target.id === 'mark-all-read-btn') {
            e.preventDefault();
            markAsRead([]); // Array vacío para marcar todas
        }
    });

    // Marcar como leída al abrir el dropdown
    if (notificationsDropdown) {
        notificationsDropdown.addEventListener('show.bs.dropdown', () => {
            setTimeout(() => markAsRead([]), 3000); // Marcar como leídas 3 segundos después de abrir
        });
    }

    // Iniciar el proceso
    fetchNotifications();
    setInterval(fetchNotifications, 60000); // Refrescar cada 60 segundos
});