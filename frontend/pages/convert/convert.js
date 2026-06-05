const DISCIPLINE = { piano:"Фортепиано", guitar:"Гитара", vocals:"Вокал", violin:"Скрипка", drums:"Барабаны", other:"Другое" };
const CONTACT = { parent:"Родитель", student:"Сам ученик", other:"Другое" };

const leadIdInput = document.getElementById('lead-id-input');
const loadBtn = document.getElementById('load-btn');
const leadInfo = document.getElementById('lead-info');
const form = document.getElementById('convert-form');
const teacherSel = document.getElementById('f_teacher');
const message = document.getElementById('message');

let currentLead = null;

function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }

async function loadTeachers() {
    try {
        const r = await fetch('/api/users/teachers');
        const teachers = await r.json();
        teacherSel.innerHTML = '<option value="">— не назначен —</option>' +
            teachers.map(t => {
                const fio = [t.last_name, t.first_name].filter(Boolean).join(' ');
                return `<option value="${t.id}">${esc(fio)} (${esc(t.email)})</option>`;
            }).join('');
    } catch(e) { /* список останется пустым */ }
}

async function loadLead(id) {
    message.classList.add('hidden');
    try {
        const r = await fetch('/api/leads/' + id);
        if (!r.ok) throw new Error(r.status === 404 ? 'Лид не найден' : 'HTTP ' + r.status);
        const l = await r.json();
        currentLead = l;

        leadInfo.innerHTML = `
            <h3>Заявка №${l.id}</h3>
            <div class="row"><span>Контакт</span><span>${esc(l.contact_full_name)} (${esc(CONTACT[l.contact_type]||l.contact_type)})</span></div>
            <div class="row"><span>ФИО ученика</span><span>${esc(l.student_full_name || '—')}</span></div>
            <div class="row"><span>Инструмент</span><span>${esc(l.discipline ? l.discipline.name : '—')}</span></div>
            <div class="row"><span>Филиал</span><span>${esc(l.preferred_branch || '—')}</span></div>
            <div class="row"><span>Статус</span><span>${esc(l.status)}</span></div>
        `;
        leadInfo.classList.remove('hidden');

        if (l.status === 'converted') {
            message.textContent = 'Этот лид уже сконвертирован в ученика';
            message.className = 'message error';
            form.classList.add('hidden');
            return;
        }

        // Предзаполняем форму: ФИО ученика (не родителя), филиал
        document.getElementById('f_full_name').value = l.student_full_name
            || (l.contact_type === 'student' ? l.contact_full_name : '');
        document.getElementById('f_branch').value = l.preferred_branch || '';
        document.getElementById('f_enrollment').value = new Date().toISOString().slice(0,10);
        form.classList.remove('hidden');
    } catch(e) {
        leadInfo.classList.add('hidden');
        form.classList.add('hidden');
        message.textContent = 'Ошибка: ' + e.message;
        message.className = 'message error';
    }
}

loadBtn.addEventListener('click', () => {
    if (leadIdInput.value) loadLead(leadIdInput.value);
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    message.classList.add('hidden');

    const payload = {
        full_name: document.getElementById('f_full_name').value.trim() || null,
        teacher_id: teacherSel.value ? parseInt(teacherSel.value, 10) : null,
        branch: document.getElementById('f_branch').value.trim() || null,
        enrollment_date: document.getElementById('f_enrollment').value,
    };

    try {
        const r = await fetch('/api/leads/' + currentLead.id + '/convert-to-student', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await r.json();
        if (r.ok) {
            message.innerHTML = `Ученик зачислен (№${data.id}: ${esc(data.student_full_name)}). ` +
                `<a href="/students-list">Перейти к списку учеников</a>`;
            message.className = 'message success';
            form.classList.add('hidden');
            loadLead(currentLead.id); // обновим инфо (статус станет converted)
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

// Автозагрузка по ?lead_id=N
loadTeachers();
const urlId = new URLSearchParams(location.search).get('lead_id');
if (urlId) { leadIdInput.value = urlId; loadLead(urlId); }
