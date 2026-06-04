Auth.requireRole(['branch_admin', 'admin']);

const tbody = document.getElementById('pays-tbody');
const authWarn = document.getElementById('auth-warn');

const METHODS = { cash:"Наличные", card:"Карта", transfer:"Перевод" };

function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function money(v){ return Number(v).toLocaleString('ru-RU') + ' ₽'; }
function fmtDate(iso){ if(!iso) return ''; return new Date(iso).toLocaleDateString('ru-RU'); }

// JWT сохраняется при входе в localStorage. Проверить ключ в login.js, если не найдётся.
function getToken() {
    return localStorage.getItem('token')
        || localStorage.getItem('access_token')
        || localStorage.getItem('jwt') || '';
}

function authHeaders() {
    const t = getToken();
    return t ? { 'Authorization': 'Bearer ' + t } : {};
}

async function loadPending() {
    if (!getToken()) authWarn.classList.remove('hidden');
    tbody.innerHTML = '<tr><td colspan="7" class="empty">Загрузка...</td></tr>';
    try {
        const r = await Auth.apiFetch('/api/payments?status=pending');
        const pays = await r.json();
        if (!pays.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty">Нет платежей в ожидании</td></tr>';
            return;
        }
        tbody.innerHTML = pays.map(p => `
            <tr data-id="${p.id}">
                <td>${p.id}</td>
                <td>${fmtDate(p.payment_date)}</td>
                <td>${esc(p.student_name||'—')}</td>
                <td>${esc(p.plan_name||'—')}</td>
                <td>${money(p.amount)}</td>
                <td>${esc(METHODS[p.method]||p.method)}</td>
                <td>
                    <button class="btn-ok" data-act="confirm" data-id="${p.id}">Подтвердить</button>
                    <button class="btn-no" data-act="reject" data-id="${p.id}">Отклонить</button>
                </td>
            </tr>`).join('');

        document.querySelectorAll('button[data-act]').forEach(b => {
            b.addEventListener('click', () => act(b.dataset.id, b.dataset.act));
        });
    } catch(e) {
        tbody.innerHTML = `<tr><td colspan="7" class="empty">Ошибка: ${e.message}</td></tr>`;
    }
}

async function act(id, action) {
    if (!getToken()) {
        alert('Сначала войдите как администратор (/login)');
        return;
    }
    try {
        const r = await Auth.apiFetch(`/api/payments/${id}/${action}`, {
            method: 'POST',
            headers: authHeaders(),
        });
        if (r.ok) {
            loadPending();  // строка исчезнет — она больше не pending
        } else if (r.status === 401) {
            alert('Нужно войти как администратор. Перейдите на /login');
            authWarn.classList.remove('hidden');
        } else if (r.status === 403) {
            alert('Недостаточно прав: подтверждать может только администратор');
        } else {
            const data = await r.json().catch(()=>({}));
            alert('Ошибка: ' + (data.detail || r.status));
        }
    } catch(e) {
        alert('Сетевая ошибка: ' + e.message);
    }
}

loadPending();
