const form = document.getElementById('employee-form');
const messageEl = document.getElementById('message');
const roleSelect = document.getElementById('role_id');

function showMessage(text, type = 'success') {
    messageEl.textContent = text;
    messageEl.className = `message ${type}`;
    messageEl.classList.remove('hidden');
}

// Загружаем список ролей и заполняем выпадающий список
async function loadRoles() {
    try {
        const response = await fetch('/api/roles');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const roles = await response.json();

        if (roles.length === 0) {
            roleSelect.innerHTML = '<option value="">Сначала создайте роли</option>';
            return;
        }

        roleSelect.innerHTML = '<option value="">— выберите роль —</option>' +
            roles.map(r => `<option value="${r.id}">${escapeHtml(r.name)}</option>`).join('');
    } catch (err) {
        roleSelect.innerHTML = `<option value="">Ошибка загрузки: ${err.message}</option>`;
    }
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function collectFormData() {
    const fd = new FormData(form);
    const data = {};
    for (const [key, rawValue] of fd.entries()) {
        const value = typeof rawValue === 'string' ? rawValue.trim() : rawValue;
        if (value === '') continue;
        data[key] = value;
    }
    if (data.role_id) {
        data.role_id = parseInt(data.role_id, 10);
    }
    return data;
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    messageEl.classList.add('hidden');

    const payload = collectFormData();

    try {
        const response = await fetch('/api/employees', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (response.ok) {
            const emp = await response.json();
            showMessage(
                `Сотрудник №${emp.id} (${emp.full_name}, ${emp.role.name}) успешно создан`,
                'success'
            );
            form.reset();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } else {
            const error = await response.json();
            let text;
            if (Array.isArray(error.detail)) {
                text = error.detail.map(e => `${e.loc.slice(-1)[0]}: ${e.msg}`).join('; ');
            } else {
                text = error.detail || 'Неизвестная ошибка';
            }
            showMessage(`Ошибка: ${text}`, 'error');
        }
    } catch (err) {
        showMessage(`Сетевая ошибка: ${err.message}`, 'error');
    }
});

loadRoles();