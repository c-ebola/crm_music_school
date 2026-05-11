const API_BASE = '/api/roles';

function initApp() {
    const form = document.getElementById('role-form');
    const messageEl = document.getElementById('message');
    const refreshBtn = document.getElementById('refresh-btn');
    const tbody = document.getElementById('roles-tbody');

    if (!form || !messageEl || !refreshBtn || !tbody) {
        console.error('Не найден один из элементов DOM');
        return;
    }

    function showMessage(text, type = 'success') {
        messageEl.textContent = text;
        messageEl.className = `message ${type}`;
        setTimeout(() => messageEl.classList.add('hidden'), 4000);
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    async function loadRoles() {
        tbody.innerHTML = '<tr><td colspan="3" class="empty">Загрузка...</td></tr>';
        try {
            const response = await fetch(API_BASE);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const roles = await response.json();

            if (roles.length === 0) {
                tbody.innerHTML = '<tr><td colspan="3" class="empty">Ролей пока нет</td></tr>';
                return;
            }

            tbody.innerHTML = roles.map(r => `
                <tr>
                    <td>${r.id}</td>
                    <td><code>${escapeHtml(r.code)}</code></td>
                    <td>${escapeHtml(r.name)}</td>
                </tr>
            `).join('');
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="3" class="empty">Ошибка: ${err.message}</td></tr>`;
        }
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);
        const payload = {
            code: formData.get('code').trim(),
            name: formData.get('name').trim(),
        };

        try {
            const response = await fetch(API_BASE, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (response.ok) {
                const role = await response.json();
                showMessage(`Роль "${role.name}" создана (id=${role.id})`, 'success');
                form.reset();
                await loadRoles();
            } else {
                const error = await response.json();
                const detail = error.detail || 'Неизвестная ошибка';
                showMessage(`Ошибка: ${typeof detail === 'string' ? detail : JSON.stringify(detail)}`, 'error');
            }
        } catch (err) {
            showMessage(`Сетевая ошибка: ${err.message}`, 'error');
        }
    });

    refreshBtn.addEventListener('click', loadRoles);

    loadRoles();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
