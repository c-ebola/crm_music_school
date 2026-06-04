Auth.requireRole(['manager', 'branch_admin', 'admin']);

const form = document.getElementById('lead-form');
const messageEl = document.getElementById('message');

function showMessage(text, type = 'success') {
    messageEl.textContent = text;
    messageEl.className = `message ${type}`;
    messageEl.classList.remove('hidden');
}

async function loadDisciplines() {
    const sel = document.getElementById('discipline_id');
    try {
        const r = await Auth.apiFetch('/api/disciplines?only_active=true');
        const list = await r.json();
        sel.innerHTML = '<option value="">— выберите —</option>' +
            list.map(d => `<option value="${d.id}">${d.name}</option>`).join('');
    } catch (e) {
        sel.innerHTML = '<option value="">Ошибка загрузки дисциплин</option>';
    }
}

loadDisciplines();

function collectFormData() {
    const fd = new FormData(form);
    const data = {};
    for (const [key, rawValue] of fd.entries()) {
        const value = typeof rawValue === 'string' ? rawValue.trim() : rawValue;
        if (value === '') continue;
        data[key] = value;
    }
    if (data.student_age) data.student_age = parseInt(data.student_age, 10);
    if (data.discipline_id) data.discipline_id = parseInt(data.discipline_id, 10);
    return data;
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    messageEl.classList.add('hidden');

    const payload = collectFormData();

    try {
        const response = await Auth.apiFetch('/api/leads', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (response.ok) {
            const lead = await response.json();
            showMessage(`Лид №${lead.id} (${lead.contact_full_name}) успешно создан`, 'success');
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
