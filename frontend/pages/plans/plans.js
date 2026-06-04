Auth.requireRole(['accountant', 'admin']);

const form = document.getElementById('plan-form');
const tbody = document.getElementById('plans-tbody');
const message = document.getElementById('message');

function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function money(v){ return Number(v).toLocaleString('ru-RU') + ' ₽'; }

async function loadPlans() {
    tbody.innerHTML = '<tr><td colspan="7" class="empty">Загрузка...</td></tr>';
    try {
        const r = await Auth.apiFetch('/api/subscription-plans');
        const plans = await r.json();
        if (!plans.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty">Абонементов пока нет</td></tr>';
            return;
        }
        tbody.innerHTML = plans.map(p => `
            <tr>
                <td>${p.id}</td>
                <td>${esc(p.name)}</td>
                <td>${p.lessons_count}</td>
                <td class="price">${money(p.price)}</td>
                <td>${p.duration_days} дн.</td>
                <td><span class="badge ${p.is_active ? 'on':'off'}">${p.is_active ? 'Активен':'Выключен'}</span></td>
                <td><button class="btn-ghost toggle" data-id="${p.id}" data-active="${p.is_active}">${p.is_active ? 'Выключить':'Включить'}</button></td>
            </tr>
        `).join('');
        document.querySelectorAll('.toggle').forEach(b => {
            b.addEventListener('click', () => togglePlan(b.dataset.id, b.dataset.active === 'true'));
        });
    } catch(e) {
        tbody.innerHTML = `<tr><td colspan="7" class="empty">Ошибка: ${e.message}</td></tr>`;
    }
}

async function togglePlan(id, isActive) {
    try {
        await Auth.apiFetch('/api/subscription-plans/' + id, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: !isActive }),
        });
        loadPlans();
    } catch(e) { alert('Ошибка: ' + e.message); }
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    message.classList.add('hidden');
    const payload = {
        name: document.getElementById('f_name').value.trim(),
        lessons_count: parseInt(document.getElementById('f_lessons').value, 10),
        price: parseFloat(document.getElementById('f_price').value),
        duration_days: parseInt(document.getElementById('f_duration').value, 10),
        is_active: document.getElementById('f_active').checked,
        description: document.getElementById('f_description').value.trim() || null,
    };
    try {
        const r = await Auth.apiFetch('/api/subscription-plans', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (r.ok) {
            message.textContent = 'Абонемент добавлен';
            message.className = 'message success';
            form.reset();
            document.getElementById('f_active').checked = true;
            loadPlans();
        } else {
            const err = await r.json();
            const detail = Array.isArray(err.detail) ? err.detail.map(x=>x.msg).join('; ') : (err.detail||'Ошибка');
            message.textContent = 'Ошибка: ' + detail;
            message.className = 'message error';
        }
    } catch(e) {
        message.textContent = 'Сетевая ошибка: ' + e.message;
        message.className = 'message error';
    }
});

loadPlans();
