Auth.requireRole(['methodist', 'branch_admin', 'admin']);

const QUANTS = 10;
const dayInput = document.getElementById('day');
const gridBody = document.getElementById('grid-body');

// модал добавления в квант
const overlay = document.getElementById('overlay');
const lessonSel = document.getElementById('m_lesson');
const roomSel = document.getElementById('m_room');
const modalMessage = document.getElementById('modal-message');

// модал учеников
const stOverlay = document.getElementById('students-overlay');
const stTitle = document.getElementById('st-title');
const stInfo = document.getElementById('st-info');
const stCapacity = document.getElementById('st-capacity');
const stList = document.getElementById('st-list');
const stEligible = document.getElementById('st-eligible');
const stMessage = document.getElementById('st-message');

let lessonsCache = [];
let currentQuant = null;
let currentEntries = [];
let currentSession = null;

function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function pad(n){ return String(n).padStart(2,'0'); }
function teacherName(t){ return t ? [t.last_name, t.first_name].filter(Boolean).join(' ') : ''; }

function quantTime(q) {
    const startMin = (q - 1) * 60;
    const sTotal = 9 * 60 + startMin;
    const eTotal = sTotal + 45;
    return `${pad(Math.floor(sTotal/60))}:${pad(sTotal%60)}–${pad(Math.floor(eTotal/60))}:${pad(eTotal%60)}`;
}

async function loadDicts() {
    try {
        const [lr, rr] = await Promise.all([
            Auth.apiFetch('/api/lessons'),
            Auth.apiFetch('/api/rooms?only_active=true'),
        ]);
        lessonsCache = await lr.json();
        const rooms = await rr.json();
        lessonSel.innerHTML = lessonsCache.map(l => {
            const disc = l.discipline ? l.discipline.name : '—';
            const t = teacherName(l.teacher);
            return `<option value="${l.id}">${esc(disc)}${t ? ' — ' + esc(t) : ''}${l.lesson_type ? ' ('+esc(l.lesson_type)+')' : ''}</option>`;
        }).join('') || '<option value="">Нет занятий — создайте сначала</option>';
        roomSel.innerHTML = '<option value="">— без кабинета —</option>' +
            rooms.map(r => `<option value="${r.id}">${esc(r.name)}${r.branch ? ' ('+esc(r.branch)+')' : ''}</option>`).join('');
    } catch(e) {}
}

async function loadGrid() {
    const day = dayInput.value;
    try {
        const r = await Auth.apiFetch('/api/schedule?day=' + day);
        currentEntries = await r.json();
    } catch(e) { currentEntries = []; }

    const byQuant = {};
    currentEntries.forEach(e => { (byQuant[e.quant] = byQuant[e.quant] || []).push(e); });

    let html = '';
    for (let q = 1; q <= QUANTS; q++) {
        const items = (byQuant[q] || []).map(e => {
            const s = e.session;
            const disc = s && s.lesson && s.lesson.discipline ? s.lesson.discipline.name : '—';
            const t = s && s.lesson ? teacherName(s.lesson.teacher) : '';
            const room = s && s.room ? s.room.name : 'без кабинета';
            return `<div class="sess" data-entry="${e.id}">
                <button class="del" data-id="${e.id}" title="Убрать из расписания">&times;</button>
                <div class="disc">${esc(disc)}</div>
                <div class="meta">${esc(t)} · ${esc(room)}</div>
            </div>`;
        }).join('');
        html += `<tr>
            <td class="qtime">Квант ${q}<br>${quantTime(q)}</td>
            <td class="slot">${items || '<span style="color:#aaa;">—</span>'}</td>
            <td><button class="add-btn" data-quant="${q}">+ Добавить</button></td>
        </tr>`;
    }
    gridBody.innerHTML = html;

    document.querySelectorAll('.add-btn').forEach(b =>
        b.addEventListener('click', () => openAddModal(parseInt(b.dataset.quant, 10))));
    document.querySelectorAll('.sess .del').forEach(b =>
        b.addEventListener('click', (ev) => { ev.stopPropagation(); removeEntry(b.dataset.id); }));
    document.querySelectorAll('.sess').forEach(card =>
        card.addEventListener('click', () => {
            const entry = currentEntries.find(x => String(x.id) === card.dataset.entry);
            if (entry && entry.session) openStudentsModal(entry.session);
        }));
}

// добавление в квант
function openAddModal(quant) {
    currentQuant = quant;
    modalMessage.classList.add('hidden');
    document.getElementById('modal-title').textContent = `Добавить занятие — квант ${quant} (${quantTime(quant)})`;
    overlay.classList.add('show');
}
function closeAddModal() { overlay.classList.remove('show'); currentQuant = null; }
document.getElementById('m_cancel').addEventListener('click', closeAddModal);
overlay.addEventListener('click', e => { if (e.target === overlay) closeAddModal(); });

document.getElementById('m_save').addEventListener('click', async () => {
    modalMessage.classList.add('hidden');
    if (!lessonSel.value) { modalMessage.textContent = 'Выберите занятие'; modalMessage.className = 'message error'; return; }
    const payload = {
        day: dayInput.value, quant: currentQuant,
        lesson_id: parseInt(lessonSel.value, 10),
        room_id: roomSel.value ? parseInt(roomSel.value, 10) : null,
    };
    try {
        const r = await Auth.apiFetch('/api/schedule/add-session', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
        });
        if (r.ok) { closeAddModal(); loadGrid(); }
        else { const err = await r.json(); modalMessage.textContent = 'Ошибка: ' + (err.detail || r.status); modalMessage.className = 'message error'; }
    } catch(e) { modalMessage.textContent = 'Сетевая ошибка: ' + e.message; modalMessage.className = 'message error'; }
});

async function removeEntry(id) {
    try { await Auth.apiFetch('/api/schedule/' + id, { method: 'DELETE' }); loadGrid(); }
    catch(e) { alert('Ошибка: ' + e.message); }
}

// ученики занятия
function openStudentsModal(session) {
    currentSession = session;
    stMessage.classList.add('hidden');
    const disc = session.lesson && session.lesson.discipline ? session.lesson.discipline.name : '—';
    const room = session.room ? session.room.name : 'без кабинета';
    const branch = session.room && session.room.branch ? session.room.branch : '—';
    stTitle.textContent = `Ученики: ${disc}`;
    const lvl = session.lesson && session.lesson.level ? session.lesson.level : 'любой';
    stInfo.textContent = `Кабинет: ${room} · Филиал: ${branch} · Уровень: ${lvl} · ${teacherName(session.lesson ? session.lesson.teacher : null)}`;
    stOverlay.classList.add('show');
    refreshStudents();
}
function closeStudentsModal() { stOverlay.classList.remove('show'); currentSession = null; }
document.getElementById('st-close').addEventListener('click', closeStudentsModal);
stOverlay.addEventListener('click', e => { if (e.target === stOverlay) closeStudentsModal(); });

async function refreshStudents() {
    const sid = currentSession.id;
    const maxStudents = currentSession.lesson ? currentSession.lesson.max_students : null;
    let enrolled = [];
    try {
        const r = await Auth.apiFetch('/api/session-students?session_id=' + sid);
        enrolled = await r.json();
    } catch(e) {}

    stCapacity.textContent = `Записано: ${enrolled.length}${maxStudents != null ? ' из ' + maxStudents : ''}`;

    stList.innerHTML = enrolled.length ? enrolled.map(s => `
        <div style="display:flex; align-items:center; gap:8px; padding:6px 0; border-bottom:1px solid #eee;">
            <label style="flex:1; display:flex; align-items:center; gap:8px;">
                <input type="checkbox" data-id="${s.id}" class="att" ${s.attended ? 'checked' : ''}>
                ${esc(s.student_name || ('Ученик №' + s.student_id))}
            </label>
            <button class="btn-no" data-id="${s.id}" style="padding:2px 10px;">Убрать</button>
        </div>`).join('') : '<div style="color:#aaa; padding:6px 0;">Никто не записан</div>';

    document.querySelectorAll('.att').forEach(c =>
        c.addEventListener('change', () => setAttended(c.dataset.id, c.checked)));
    stList.querySelectorAll('.btn-no').forEach(b =>
        b.addEventListener('click', () => unenroll(b.dataset.id)));

    // отфильтрованные кандидаты: дисциплина занятия + филиал кабинета, минус уже записанные
    const disciplineId = currentSession.lesson && currentSession.lesson.discipline ? currentSession.lesson.discipline.id : null;
    const branch = currentSession.room ? currentSession.room.branch : null;
    const params = new URLSearchParams({ is_student: 'true' });
    if (disciplineId) params.set('discipline_id', disciplineId);
    if (branch) params.set('branch', branch);
    const level = currentSession.lesson ? currentSession.lesson.level : null;
    if (level) params.set('level', level);

    let candidates = [];
    try { candidates = await (await Auth.apiFetch('/api/leads?' + params.toString())).json(); } catch(e) {}
    const enrolledIds = new Set(enrolled.map(s => s.student_id));
    candidates = candidates.filter(c => !enrolledIds.has(c.id));

    stEligible.innerHTML = candidates.length
        ? candidates.map(c => `<option value="${c.id}">${esc(c.student_full_name || c.contact_full_name)}</option>`).join('')
        : '<option value="">Нет подходящих учеников</option>';
}

document.getElementById('st-enroll').addEventListener('click', async () => {
    stMessage.classList.add('hidden');
    if (!stEligible.value) { stMessage.textContent = 'Нет ученика для записи'; stMessage.className = 'message error'; return; }
    try {
        const r = await Auth.apiFetch('/api/session-students', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: currentSession.id, student_id: parseInt(stEligible.value, 10) }),
        });
        if (r.ok) { refreshStudents(); }
        else { const err = await r.json(); stMessage.textContent = 'Ошибка: ' + (err.detail || r.status); stMessage.className = 'message error'; }
    } catch(e) { stMessage.textContent = 'Сетевая ошибка: ' + e.message; stMessage.className = 'message error'; }
});

async function setAttended(id, attended) {
    try {
        await Auth.apiFetch('/api/session-students/' + id, {
            method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ attended }),
        });
    } catch(e) { alert('Ошибка: ' + e.message); }
}

async function unenroll(id) {
    try { await Auth.apiFetch('/api/session-students/' + id, { method: 'DELETE' }); refreshStudents(); }
    catch(e) { alert('Ошибка: ' + e.message); }
}

dayInput.addEventListener('change', loadGrid);
dayInput.value = new Date().toISOString().slice(0, 10);
loadDicts();
loadGrid();
