Auth.requireRole(['admin']);

const form = document.getElementById('user-form');
const messageEl = document.getElementById('message');
const roleSelect = document.getElementById('role_id');
const tbody = document.getElementById('users-tbody');

function showMessage(text, type) {
    messageEl.textContent = text;
    messageEl.className = 'message ' + type;
    messageEl.classList.remove('hidden');
}
function escapeHtml(s) { const d = document.createElement('div'); d.textContent = s == null ? '' : s; return d.innerHTML; }

async function loadRoles() {
    try {
        const resp = await Auth.apiFetch('/api/roles');
        const roles = await resp.json();
        roleSelect.innerHTML = '<option value="">— выберите роль —</option>' +
            roles.map(r => `<option value="${r.id}">${escapeHtml(r.name)}</option>`).join('');
    } catch (e) { /* ignore */ }
}

async function loadBranches() {
    const sel = document.getElementById('user_branch');
    try {
        const resp = await Auth.apiFetch('/api/branches?kind=school&only_active=true');
        const list = await resp.json();
        sel.innerHTML = '<option value="">— не выбран —</option>' +
            (Array.isArray(list)?list:[]).map(b => `<option value="${b.id}">${escapeHtml(b.name)}${b.city ? ' ('+escapeHtml(b.city)+')' : ''}</option>`).join('');
    } catch (e) { /* ignore */ }
}

async function loadUsers() {
    tbody.innerHTML = '<tr><td colspan="5" class="empty">Загрузка...</td></tr>';
    try {
        const resp = await Auth.apiFetch('/api/users');
        if (resp.status === 403) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty">Нет прав на просмотр (нужен админ)</td></tr>';
            return;
        }
        const users = await resp.json();
        if (!users.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty">Пользователей нет</td></tr>';
            return;
        }
        tbody.innerHTML = users.map(u => `
            <tr>
                <td>${u.id}</td>
                <td>${escapeHtml(u.full_name)}</td>
                <td>${escapeHtml(u.email)}</td>
                <td>${escapeHtml(u.role.name)}${u.is_superuser ? ' ★' : ''}</td>
                <td>${u.is_active ? 'активен' : 'отключён'}</td>
            </tr>`).join('');
    } catch (e) { /* 401 уже увёл на логин */ }
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    messageEl.classList.add('hidden');
    const fd = new FormData(form);
    const payload = {
        last_name: fd.get('last_name').trim(),
        first_name: fd.get('first_name').trim(),
        middle_name: fd.get('middle_name').trim() || null,
        phone: fd.get('phone').trim() || null,
        email: fd.get('email').trim(),
        password: fd.get('password'),
        role_id: parseInt(fd.get('role_id'), 10),
        is_active: document.getElementById('is_active').checked,
        is_superuser: document.getElementById('is_superuser').checked,
        branch_id: document.getElementById('user_branch').value ? parseInt(document.getElementById('user_branch').value, 10) : null,
    };
    try {
        const resp = await Auth.apiFetch('/api/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (resp.ok) {
            const u = await resp.json();
            showMessage(`Пользователь ${u.full_name} (${u.role.name}) создан`, 'success');
            form.reset();
            document.getElementById('is_active').checked = true;
            await loadUsers();
        } else {
            const err = await resp.json();
            const detail = Array.isArray(err.detail)
                ? err.detail.map(x => `${x.loc.slice(-1)[0]}: ${x.msg}`).join('; ')
                : (err.detail || 'Ошибка');
            showMessage('Ошибка: ' + detail, 'error');
        }
    } catch (err) {
        showMessage('Сетевая ошибка: ' + err.message, 'error');
    }
});

loadRoles();
loadBranches();
loadUsers();
