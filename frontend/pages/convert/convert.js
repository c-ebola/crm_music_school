Auth.requireRole(['manager', 'branch_admin', 'admin']);

const CONTACT = { parent: "Родитель", student: "Сам ученик", other: "Другое" };

const leadSelect = document.getElementById('lead-select');
const leadInfo = document.getElementById('lead-info');
const form = document.getElementById('convert-form');
const teacherSel = document.getElementById('f_teacher');
const message = document.getElementById('message');

let currentLead = null;

function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function leadName(l){ return l.student_full_name || l.contact_full_name || ('Лид #'+l.id); }

async function loadTeachers() {
    try {
        const r = await Auth.apiFetch('/api/users/teachers');
        const teachers = await r.json();
        teacherSel.innerHTML = '<option value="">— не назначен —</option>' +
            teachers.map(t => {
                const fio = [t.last_name, t.first_name].filter(Boolean).join(' ');
                return `<option value="${t.id}">${esc(fio)} (${esc(t.email)})</option>`;
            }).join('');
    } catch(e) {}
}

async function loadBranches() {
    const sel = document.getElementById('f_branch');
    try {
        const r = await Auth.apiFetch('/api/branches?kind=school&only_active=true');
        const list = await r.json();
        sel.innerHTML = '<option value="">— не выбран —</option>' +
            (Array.isArray(list)?list:[]).map(b => `<option value="${b.id}">${esc(b.name)}${b.city ? ' ('+esc(b.city)+')' : ''}</option>`).join('');
    } catch (e) { sel.innerHTML = '<option value="">Ошибка загрузки</option>'; }
}

async function loadLeads() {
    try {
        const r = await Auth.apiFetch('/api/leads');
        const leads = await r.json();
        const open = (Array.isArray(leads) ? leads : []).filter(l => l.status !== 'converted' && !l.is_student);
        leadSelect.innerHTML = open.length
            ? '<option value="">— выберите лида —</option>' + open.map(l =>
                `<option value="${l.id}">№${l.id} · ${esc(leadName(l))}${l.discipline ? ' · ' + esc(l.discipline.name) : ''}</option>`).join('')
            : '<option value="">Нет несконвертированных лидов</option>';
    } catch(e) {
        leadSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
    }
}

async function loadLead(id) {
    message.classList.add('hidden');
    try {
        const r = await Auth.apiFetch('/api/leads/' + id);
        if (!r.ok) throw new Error(r.status === 404 ? 'Лид не найден' : 'HTTP ' + r.status);
        const l = await r.json();
        currentLead = l;

        leadInfo.innerHTML = `
            <h3>Заявка №${l.id}</h3>
            <div class="row"><span>Контакт</span><span>${esc(l.contact_full_name)} (${esc(CONTACT[l.contact_type]||l.contact_type)})</span></div>
            <div class="row"><span>ФИО ученика</span><span>${esc(l.student_full_name || '—')}</span></div>
            <div class="row"><span>Инструмент</span><span>${esc(l.discipline ? l.discipline.name : '—')}</span></div>
            <div class="row"><span>Филиал</span><span>${esc(l.branch ? l.branch.name : '—')}</span></div>
            <div class="row"><span>Статус</span><span>${esc(l.status)}</span></div>
        `;
        leadInfo.classList.remove('hidden');

        if (l.status === 'converted') {
            message.textContent = 'Этот лид уже сконвертирован в ученика';
            message.className = 'message error';
            form.classList.add('hidden');
            return;
        }

        document.getElementById('f_full_name').value = l.student_full_name
            || (l.contact_type === 'student' ? l.contact_full_name : '');
        document.getElementById('f_branch').value = l.branch_id ? String(l.branch_id) : '';
        document.getElementById('f_enrollment').value = new Date().toISOString().slice(0,10);
        form.classList.remove('hidden');
    } catch(e) {
        leadInfo.classList.add('hidden');
        form.classList.add('hidden');
        message.textContent = 'Ошибка: ' + e.message;
        message.className = 'message error';
    }
}

leadSelect.addEventListener('change', () => {
    if (leadSelect.value) loadLead(leadSelect.value);
    else { leadInfo.classList.add('hidden'); form.classList.add('hidden'); }
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    message.classList.add('hidden');
    if (!currentLead) { message.textContent = 'Сначала выберите лида'; message.className = 'message error'; return; }
    const payload = {
        full_name: document.getElementById('f_full_name').value.trim() || null,
        teacher_id: teacherSel.value ? parseInt(teacherSel.value, 10) : null,
        branch_id: document.getElementById('f_branch').value ? parseInt(document.getElementById('f_branch').value, 10) : null,
        enrollment_date: document.getElementById('f_enrollment').value,
    };
    try {
        const r = await Auth.apiFetch('/api/leads/' + currentLead.id + '/convert-to-student', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
        });
        const data = await r.json();
        if (r.ok) {
            message.innerHTML = `Ученик зачислен (№${data.id}: ${esc(data.student_full_name)}).`;
            message.className = 'message success';
            form.classList.add('hidden');
            leadInfo.classList.add('hidden');
            await loadLeads();
            leadSelect.value = '';
        } else {
            const detail = Array.isArray(data.detail)
                ? data.detail.map(x => x.msg).join('; ') : (data.detail || 'Ошибка');
            message.textContent = 'Ошибка: ' + detail;
            message.className = 'message error';
        }
    } catch(e) {
        message.textContent = 'Сетевая ошибка: ' + e.message;
        message.className = 'message error';
    }
});

(async () => {
    await loadTeachers();
    await loadBranches();
    await loadLeads();
    const urlId = new URLSearchParams(location.search).get('lead_id');
    if (urlId) { leadSelect.value = urlId; loadLead(urlId); }
})();
