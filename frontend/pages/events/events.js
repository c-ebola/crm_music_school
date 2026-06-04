Auth.requireRole(['methodist', 'branch_admin', 'admin']);

const STATUS = { planned: 'Запланирован', completed: 'Проведён', cancelled: 'Отменён' };

const $ = id => document.getElementById(id);
function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function teacherName(t){ return t ? [t.last_name, t.first_name].filter(Boolean).join(' ') : ''; }

let teachers = [], rooms = [], students = [], instruments = [];
let currentEvent = null;

async function loadDicts(){
    try {
        const [tr, rr, sr, ir] = await Promise.all([
            Auth.apiFetch('/api/users/teachers'),
            Auth.apiFetch('/api/rooms?only_active=true'),
            Auth.apiFetch('/api/leads?is_student=true'),
            Auth.apiFetch('/api/instruments?only_active=true'),
        ]);
        const t = await tr.json(), r = await rr.json(), s = await sr.json(), i = await ir.json();
        teachers = Array.isArray(t) ? t : [];
        rooms = Array.isArray(r) ? r : [];
        students = Array.isArray(s) ? s : [];
        instruments = Array.isArray(i) ? i : [];
    } catch(e){ teachers = []; rooms = []; students = []; instruments = []; }
}

function teacherOpts(){
    return '<option value="">— без преподавателя —</option>' +
        teachers.map(t => `<option value="${t.id}">${esc(teacherName(t) || t.email)}</option>`).join('');
}
function roomOpts(){
    return '<option value="">— без кабинета —</option>' +
        rooms.map(r => `<option value="${r.id}">${esc(r.name)}${r.branch ? ' ('+esc(r.branch)+')' : ''}</option>`).join('');
}
function studentOpts(){
    return '<option value="">— выберите ученика —</option>' +
        students.map(s => `<option value="${s.id}">${esc(s.student_full_name || s.contact_full_name)}</option>`).join('');
}
function instrumentOpts(){
    return '<option value="">— инструмент —</option>' +
        instruments.map(i => `<option value="${i.id}">${esc(i.name)}</option>`).join('');
}

// ===== переключение видов =====
function showList(){ $('view-editor').classList.add('hidden'); $('view-list').classList.remove('hidden'); }
function showEditor(){ $('view-list').classList.add('hidden'); $('view-editor').classList.remove('hidden'); }

// ===== СПИСОК =====
function openCreate(){
    $('create-message').classList.add('hidden');
    $('e_title').value = ''; $('e_desc').value = '';
    $('create-card').classList.remove('hidden');
    $('open-create').classList.add('hidden');
    $('e_title').focus();
}
function closeCreate(){
    $('create-card').classList.add('hidden');
    $('open-create').classList.remove('hidden');
}
$('open-create').addEventListener('click', openCreate);
$('cancel-create').addEventListener('click', closeCreate);

// Создать концерт → сразу открыть редактор
$('save-concert').addEventListener('click', async () => {
    const msg = $('create-message'); msg.classList.add('hidden');
    const title = $('e_title').value.trim();
    if (!title){ msg.textContent = 'Введите название концерта'; msg.className = 'message error'; return; }
    try {
        const r = await Auth.apiFetch('/api/events', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description: $('e_desc').value.trim() || null }),
        });
        if (!r.ok){ const e = await r.json().catch(()=>({})); throw new Error(e.detail || r.status); }
        const ev = await r.json();
        closeCreate();
        openEditor(ev);
    } catch(e){ msg.textContent = 'Ошибка создания концерта: ' + e.message; msg.className = 'message error'; }
});

async function loadList(){
    $('loading').classList.remove('hidden');
    let events = [];
    try {
        const r = await Auth.apiFetch('/api/events');
        const d = await r.json();
        events = Array.isArray(d) ? d : [];
    } catch(e){ events = []; }
    $('loading').classList.add('hidden');

    if (!events.length){ $('ev-list').innerHTML = '<div style="color:#aaa;">Концертов пока нет</div>'; return; }

    const perfByEvent = {};
    await Promise.all(events.map(async ev => {
        try {
            const r = await Auth.apiFetch('/api/performances?event_id=' + ev.id);
            const d = await r.json();
            perfByEvent[ev.id] = Array.isArray(d) ? d : [];
        } catch(e){ perfByEvent[ev.id] = []; }
    }));

    $('ev-list').innerHTML = events.map(ev => {
        const perfs = perfByEvent[ev.id] || [];
        const count = perfs.length;
        return `<div class="ev-card" data-ev="${ev.id}">
            <div class="top">
                <div>
                    <div style="font-weight:600; font-size:16px;">${esc(ev.title)}<span class="badge ${esc(ev.status)}">${esc(STATUS[ev.status] || ev.status)}</span></div>
                    ${ev.description ? `<div style="color:#555; font-size:13px; margin-top:2px;">${esc(ev.description)}</div>` : ''}
                    <div style="color:#777; font-size:13px; margin-top:4px;">Выступлений: ${count}</div>
                </div>
                <div style="display:flex; gap:6px; white-space:nowrap;">
                    <button class="btn-ghost ev-open" data-id="${ev.id}" style="padding:2px 10px;">Настроить</button>
                    <button class="btn-ghost ev-del" data-id="${ev.id}" style="padding:2px 10px;">Удалить</button>
                </div>
            </div>
        </div>`;
    }).join('');

    document.querySelectorAll('.ev-del').forEach(b => b.addEventListener('click', () => deleteEvent(b.dataset.id)));
    document.querySelectorAll('.ev-open').forEach(b => b.addEventListener('click', () => {
        const ev = events.find(x => String(x.id) === b.dataset.id);
        if (ev) openEditor(ev);
    }));
}

async function deleteEvent(id){
    if (!confirm('Удалить концерт со всеми выступлениями?')){ return; }
    try {
        const r = await Auth.apiFetch('/api/events/' + id, { method: 'DELETE' });
        if (r.ok){ loadList(); }
        else { const e = await r.json().catch(()=>({})); alert('Не удалось удалить: ' + (e.detail || ('HTTP ' + r.status))); }
    } catch(e){ alert('Сетевая ошибка: ' + e.message); }
}

// ===== РЕДАКТОР =====
function openEditor(ev){
    currentEvent = ev;
    $('editor-title').textContent = 'Концерт: ' + (ev.title || '');
    $('editor-desc').textContent = ev.description || '';
    $('editor-message').classList.add('hidden');
    $('pf_teacher').innerHTML = teacherOpts();
    $('pf_room').innerHTML = roomOpts();
    $('pf_notes').value = '';
    showEditor();
    refreshPerformances();
}
$('back-list').addEventListener('click', () => { showList(); loadList(); });

async function refreshPerformances(){
    const box = $('perf-list');
    box.innerHTML = '<div style="color:#aaa;">Загрузка…</div>';
    let perfs = [];
    try {
        const r = await Auth.apiFetch('/api/performances?event_id=' + currentEvent.id);
        const d = await r.json();
        perfs = Array.isArray(d) ? d : [];
    } catch(e){ perfs = []; }

    if (!perfs.length){ box.innerHTML = '<div style="color:#aaa;">Выступлений пока нет</div>'; return; }

    const performersByPerf = {};
    await Promise.all(perfs.map(async p => {
        try {
            const r = await Auth.apiFetch('/api/performance-students?performance_id=' + p.id);
            const d = await r.json();
            performersByPerf[p.id] = Array.isArray(d) ? d : [];
        } catch(e){ performersByPerf[p.id] = []; }
    }));

    box.innerHTML = perfs.map((p, i) => {
        const performers = performersByPerf[p.id] || [];
        const performersHtml = performers.length
            ? performers.map(ps => `<div style="display:flex; justify-content:space-between; align-items:center; padding:3px 0;">
                    <span>${esc(ps.student_name || ('Ученик №'+ps.student_id))}${ps.instrument_name ? ' — '+esc(ps.instrument_name) : ''}</span>
                    <button class="btn-ghost ps-del" data-id="${ps.id}" style="padding:1px 8px;">×</button>
                </div>`).join('')
            : '<div style="color:#aaa;">Исполнителей нет</div>';
        return `<div class="perf-card" data-perf="${p.id}">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div style="font-weight:600;">Выступление ${i + 1}</div>
                    <div style="color:#555; font-size:13px;">${esc(p.teacher_name || 'без преподавателя')}${p.room_name ? ' · '+esc(p.room_name) : ''}${p.notes ? ' — '+esc(p.notes) : ''}</div>
                </div>
                <button class="btn-ghost perf-del" data-id="${p.id}" style="padding:2px 10px; white-space:nowrap;">Удалить</button>
            </div>
            <div style="margin-top:8px;">${performersHtml}</div>
            <div style="display:flex; gap:6px; margin-top:8px;">
                <select class="ps-student" style="flex:2;">${studentOpts()}</select>
                <select class="ps-instrument" style="flex:1;">${instrumentOpts()}</select>
                <button class="btn-ghost ps-add" data-perf="${p.id}" style="white-space:nowrap;">+ ученик</button>
            </div>
        </div>`;
    }).join('');
}

// клики внутри списка выступлений (делегирование)
$('perf-list').addEventListener('click', (e) => {
    const t = e.target;
    if (t.classList.contains('perf-del')) deletePerformance(t.dataset.id);
    else if (t.classList.contains('ps-del')) deletePerformer(t.dataset.id);
    else if (t.classList.contains('ps-add')) {
        const card = t.closest('.perf-card');
        addPerformer(t.dataset.perf, card.querySelector('.ps-student').value, card.querySelector('.ps-instrument').value);
    }
});

// добавить выступление (создаётся сразу)
$('pf_add').addEventListener('click', async () => {
    const msg = $('editor-message'); msg.classList.add('hidden');
    const payload = {
        event_id: currentEvent.id,
        teacher_id: $('pf_teacher').value ? parseInt($('pf_teacher').value, 10) : null,
        room_id: $('pf_room').value ? parseInt($('pf_room').value, 10) : null,
        notes: $('pf_notes').value.trim() || null,
    };
    try {
        const r = await Auth.apiFetch('/api/performances', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
        });
        if (r.ok){ $('pf_teacher').value=''; $('pf_room').value=''; $('pf_notes').value=''; refreshPerformances(); }
        else { const e = await r.json().catch(()=>({})); alert('Не удалось добавить выступление: ' + (e.detail || ('HTTP ' + r.status))); }
    } catch(e){ alert('Сетевая ошибка: ' + e.message); }
});

async function addPerformer(perfId, studentId, instrumentId){
    if (!studentId){ alert('Выберите ученика'); return; }
    const payload = {
        performance_id: parseInt(perfId, 10),
        student_id: parseInt(studentId, 10),
        instrument_id: instrumentId ? parseInt(instrumentId, 10) : null,
    };
    try {
        const r = await Auth.apiFetch('/api/performance-students', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
        });
        if (r.ok){ refreshPerformances(); }
        else { const e = await r.json().catch(()=>({})); alert('Не удалось добавить ученика: ' + (e.detail || ('HTTP ' + r.status))); }
    } catch(e){ alert('Сетевая ошибка: ' + e.message); }
}

async function deletePerformance(id){
    try {
        const r = await Auth.apiFetch('/api/performances/' + id, { method: 'DELETE' });
        if (r.ok){ refreshPerformances(); }
        else { const e = await r.json().catch(()=>({})); alert('Не удалось удалить: ' + (e.detail || ('HTTP ' + r.status))); }
    } catch(e){ alert('Сетевая ошибка: ' + e.message); }
}
async function deletePerformer(id){
    try {
        const r = await Auth.apiFetch('/api/performance-students/' + id, { method: 'DELETE' });
        if (r.ok){ refreshPerformances(); }
        else { const e = await r.json().catch(()=>({})); alert('Не удалось удалить: ' + (e.detail || ('HTTP ' + r.status))); }
    } catch(e){ alert('Сетевая ошибка: ' + e.message); }
}

(async function(){
    await loadDicts();
    await loadList();
})();
