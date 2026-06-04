Auth.requireRole(['methodist', 'branch_admin', 'admin']);

const QUANTS = 10;
const dayInput = document.getElementById('day');
const gridBody = document.getElementById('grid-body');

// модал добавления занятия
const overlay = document.getElementById('overlay');
const lessonSel = document.getElementById('m_lesson');
const roomSel = document.getElementById('m_room');
const modalMessage = document.getElementById('modal-message');

// модал выбора концерта
const evOverlay = document.getElementById('ev-overlay');
const evEventSel = document.getElementById('ev_event');
const evMessage = document.getElementById('ev-message');

// модал учеников занятия
const stOverlay = document.getElementById('students-overlay');
const stTitle = document.getElementById('st-title');
const stInfo = document.getElementById('st-info');
const stCapacity = document.getElementById('st-capacity');
const stList = document.getElementById('st-list');
const stEligible = document.getElementById('st-eligible');
const stMessage = document.getElementById('st-message');

let lessonsCache = [];
let eventsCache = [];
let currentQuant = null;
let currentEntries = [];
let currentSession = null;
let canAddSession = false;
let canAddEvent = false;

// безопасная привязка: нет элемента — просто пропускаем, страница не падает
function on(id, type, fn){ const el = document.getElementById(id); if (el) el.addEventListener(type, fn); }
function onEl(el, type, fn){ if (el) el.addEventListener(type, fn); }

function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function pad(n){ return String(n).padStart(2,'0'); }
function teacherName(t){ return t ? [t.last_name, t.first_name].filter(Boolean).join(' ') : ''; }

function quantTime(q) {
    const startMin = (q - 1) * 60;
    const sTotal = 9 * 60 + startMin;
    const eTotal = sTotal + 45;
    return `${pad(Math.floor(sTotal/60))}:${pad(sTotal%60)}–${pad(Math.floor(eTotal/60))}:${pad(eTotal%60)}`;
}

async function initPerms() {
    try {
        const me = await Auth.getMe();
        const role = me && me.role ? me.role.code : null;
        const su = !!(me && me.is_superuser);
        canAddSession = role === 'methodist' || role === 'branch_admin' || role === 'admin' || su;
        canAddEvent = role === 'branch_admin' || role === 'admin' || su;
    } catch (e) {}
}

async function loadDicts() {
    try {
        const [lr, rr] = await Promise.all([
            Auth.apiFetch('/api/lessons'),
            Auth.apiFetch('/api/rooms?only_active=true'),
        ]);
        const lessonsData = await lr.json();
        const roomsData = await rr.json();
        lessonsCache = Array.isArray(lessonsData) ? lessonsData : [];
        const rooms = Array.isArray(roomsData) ? roomsData : [];
        if (lessonSel) lessonSel.innerHTML = lessonsCache.map(l => {
            const disc = l.discipline ? l.discipline.name : '—';
            const t = teacherName(l.teacher);
            return `<option value="${l.id}">${esc(disc)}${t ? ' — ' + esc(t) : ''}${l.lesson_type ? ' ('+esc(l.lesson_type)+')' : ''}</option>`;
        }).join('') || '<option value="">Нет занятий — создайте сначала</option>';
        if (roomSel) roomSel.innerHTML = '<option value="">— без кабинета —</option>' +
            rooms.map(r => `<option value="${r.id}">${esc(r.name)}${r.branch ? ' ('+esc(r.branch)+')' : ''}</option>`).join('');
    } catch(e) {}
}

async function loadGrid() {
    const day = dayInput.value;
    try {
        const r = await Auth.apiFetch('/api/schedule?day=' + day);
        const data = await r.json();
        currentEntries = Array.isArray(data) ? data : [];
    } catch(e) { currentEntries = []; }

    const byQuant = {};
    currentEntries.forEach(e => { (byQuant[e.quant] = byQuant[e.quant] || []).push(e); });

    let html = '';
    for (let q = 1; q <= QUANTS; q++) {
        const items = (byQuant[q] || []).map(e => {
            if (e.entity_type === 'event') {
                const ev = e.event || {};
                return `<div class="event" data-entry="${e.id}" style="background:#fdeecf; border-radius:8px; padding:8px 10px; margin-bottom:6px; font-size:13px; position:relative;">
                    <button class="del" data-id="${e.id}" title="Убрать из расписания" style="position:absolute; top:4px; right:8px; cursor:pointer; color:#8c1f1f; border:none; background:none; font-size:14px;">&times;</button>
                    <div style="font-weight:600;">🎵 ${esc(ev.title || 'Концерт')}</div>
                    <div style="color:#555;">Концерт${ev.description ? ' · ' + esc(ev.description) : ''}</div>
                </div>`;
            }
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

        const addButtons =
            (canAddSession ? `<button class="add-btn add-session" data-quant="${q}">+ Занятие</button>` : '') +
            (canAddEvent ? `<button class="add-btn add-event" data-quant="${q}" style="margin-top:6px; color:#8a5b00;">+ Концерт</button>` : '');

        html += `<tr>
            <td class="qtime">Квант ${q}<br>${quantTime(q)}</td>
            <td class="slot">${items || '<span style="color:#aaa;">—</span>'}</td>
            <td>${addButtons}</td>
        </tr>`;
    }
    gridBody.innerHTML = html;

    document.querySelectorAll('.add-session').forEach(b =>
        b.addEventListener('click', () => openAddModal(parseInt(b.dataset.quant, 10))));
    document.querySelectorAll('.add-event').forEach(b =>
        b.addEventListener('click', () => openEventModal(parseInt(b.dataset.quant, 10))));
    document.querySelectorAll('.del').forEach(b =>
        b.addEventListener('click', (ev) => { ev.stopPropagation(); removeEntry(b.dataset.id); }));
    document.querySelectorAll('.sess').forEach(card =>
        card.addEventListener('click', () => {
            const entry = currentEntries.find(x => String(x.id) === card.dataset.entry);
            if (entry && entry.session) openStudentsModal(entry.session);
        }));
}

// ---------- добавление ЗАНЯТИЯ ----------
function openAddModal(quant) {
    currentQuant = quant;
    if (modalMessage) modalMessage.classList.add('hidden');
    const tt = document.getElementById('modal-title');
    if (tt) tt.textContent = `Добавить занятие — квант ${quant} (${quantTime(quant)})`;
    if (overlay) overlay.classList.add('show');
}
function closeAddModal() { if (overlay) overlay.classList.remove('show'); currentQuant = null; }
on('m_cancel', 'click', closeAddModal);
onEl(overlay, 'click', e => { if (e.target === overlay) closeAddModal(); });

on('m_save', 'click', async () => {
    if (modalMessage) modalMessage.classList.add('hidden');
    if (!lessonSel || !lessonSel.value) { if (modalMessage){ modalMessage.textContent = 'Выберите занятие'; modalMessage.className = 'message error'; } return; }
    const payload = {
        day: dayInput.value, quant: currentQuant,
        lesson_id: parseInt(lessonSel.value, 10),
        room_id: roomSel && roomSel.value ? parseInt(roomSel.value, 10) : null,
    };
    try {
        const r = await Auth.apiFetch('/api/schedule/add-session', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
        });
        if (r.ok) { closeAddModal(); loadGrid(); }
        else { const err = await r.json(); if (modalMessage){ modalMessage.textContent = 'Ошибка: ' + (err.detail || r.status); modalMessage.className = 'message error'; } }
    } catch(e) { if (modalMessage){ modalMessage.textContent = 'Сетевая ошибка: ' + e.message; modalMessage.className = 'message error'; } }
});

// ---------- добавление КОНЦЕРТА (выбор существующего) ----------
async function loadEventsForSelect() {
    try {
        const r = await Auth.apiFetch('/api/events');
        const d = await r.json();
        eventsCache = Array.isArray(d) ? d : [];
    } catch(e) { eventsCache = []; }
    if (evEventSel) evEventSel.innerHTML = eventsCache.length
        ? eventsCache.map(ev => `<option value="${ev.id}">${esc(ev.title)}</option>`).join('')
        : '<option value="">Сначала создайте концерт на странице «Концерты»</option>';
}

async function openEventModal(quant) {
    currentQuant = quant;
    if (evMessage) evMessage.classList.add('hidden');
    const tt = document.getElementById('ev-title-h');
    if (tt) tt.textContent = `Добавить концерт — квант ${quant} (${quantTime(quant)})`;
    await loadEventsForSelect();
    if (evOverlay) evOverlay.classList.add('show');
}
function closeEventModal() { if (evOverlay) evOverlay.classList.remove('show'); currentQuant = null; }
on('ev_cancel', 'click', closeEventModal);
onEl(evOverlay, 'click', e => { if (e.target === evOverlay) closeEventModal(); });

on('ev_save', 'click', async () => {
    if (evMessage) evMessage.classList.add('hidden');
    if (!evEventSel || !evEventSel.value) { if (evMessage){ evMessage.textContent = 'Выберите концерт'; evMessage.className = 'message error'; } return; }
    const payload = { day: dayInput.value, quant: currentQuant, event_id: parseInt(evEventSel.value, 10) };
    try {
        const r = await Auth.apiFetch('/api/schedule/place-event', {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
        });
        if (r.ok) { closeEventModal(); loadGrid(); }
        else { const err = await r.json(); if (evMessage){ evMessage.textContent = 'Ошибка: ' + (err.detail || r.status); evMessage.className = 'message error'; } }
    } catch(e) { if (evMessage){ evMessage.textContent = 'Сетевая ошибка: ' + e.message; evMessage.className = 'message error'; } }
});

async function removeEntry(id) {
    try { await Auth.apiFetch('/api/schedule/' + id, { method: 'DELETE' }); loadGrid(); }
    catch(e) { alert('Ошибка: ' + e.message); }
}

// ---------- ученики занятия (запись на сессию) ----------
function openStudentsModal(session) {
    currentSession = session;
    if (stMessage) stMessage.classList.add('hidden');
    const disc = session.lesson && session.lesson.discipline ? session.lesson.discipline.name : '—';
    const room = session.room ? session.room.name : 'без кабинета';
    const branch = session.room && session.room.branch ? session.room.branch : '—';
    if (stTitle) stTitle.textContent = `Ученики: ${disc}`;
    const lvl = session.lesson && session.lesson.level ? session.lesson.level : 'любой';
    if (stInfo) stInfo.textContent = `Кабинет: ${room} · Филиал: ${branch} · Уровень: ${lvl} · ${teacherName(session.lesson ? session.lesson.teacher : null)}`;
    if (stOverlay) stOverlay.classList.add('show');
    refreshStudents();
}
function closeStudentsModal() { if (stOverlay) stOverlay.classList.remove('show'); currentSession = null; }
on('st-close', 'click', closeStudentsModal);
onEl(stOverlay, 'click', e => { if (e.target === stOverlay) closeStudentsModal(); });

async function refreshStudents() {
    if (!currentSession) return;
    const sid = currentSession.id;
    const maxStudents = currentSession.lesson ? currentSession.lesson.max_students : null;
    let enrolled = [];
    try {
        const r = await Auth.apiFetch('/api/session-students?session_id=' + sid);
        enrolled = await r.json();
    } catch(e) {}
    if (!Array.isArray(enrolled)) enrolled = [];

    if (stCapacity) stCapacity.textContent = `Записано: ${enrolled.length}${maxStudents != null ? ' из ' + maxStudents : ''}`;

    if (stList) stList.innerHTML = enrolled.length ? enrolled.map(s => `
        <div style="display:flex; align-items:center; gap:8px; padding:6px 0; border-bottom:1px solid #eee;">
            <label style="flex:1; display:flex; align-items:center; gap:8px;">
                <input type="checkbox" data-id="${s.id}" class="att" ${s.attended ? 'checked' : ''}>
                ${esc(s.student_name || ('Ученик №' + s.student_id))}
            </label>
            <button class="btn-no" data-id="${s.id}" style="padding:2px 10px;">Убрать</button>
        </div>`).join('') : '<div style="color:#aaa; padding:6px 0;">Никто не записан</div>';

    document.querySelectorAll('.att').forEach(c =>
        c.addEventListener('change', () => setAttended(c.dataset.id, c.checked)));
    if (stList) stList.querySelectorAll('.btn-no').forEach(b =>
        b.addEventListener('click', () => unenroll(b.dataset.id)));

    const disciplineId = currentSession.lesson && currentSession.lesson.discipline ? currentSession.lesson.discipline.id : null;
    const branch = currentSession.room ? currentSession.room.branch : null;
    const params = new URLSearchParams({ is_student: 'true' });
    if (disciplineId) params.set('discipline_id', disciplineId);
    if (branch) params.set('branch', branch);
    const level = currentSession.lesson ? currentSession.lesson.level : null;
    if (level) params.set('level', level);

    let candidates = [];
    try { candidates = await (await Auth.apiFetch('/api/leads?' + params.toString())).json(); } catch(e) {}
    if (!Array.isArray(candidates)) candidates = [];
    const enrolledIds = new Set(enrolled.map(s => s.student_id));
    candidates = candidates.filter(c => !enrolledIds.has(c.id));

    if (stEligible) stEligible.innerHTML = candidates.length
        ? candidates.map(c => `<option value="${c.id}">${esc(c.student_full_name || c.contact_full_name)}</option>`).join('')
        : '<option value="">Нет подходящих учеников</option>';
}

on('st-enroll', 'click', async () => {
    if (stMessage) stMessage.classList.add('hidden');
    if (!stEligible || !stEligible.value) { if (stMessage){ stMessage.textContent = 'Нет ученика для записи'; stMessage.className = 'message error'; } return; }
    try {
        const r = await Auth.apiFetch('/api/session-students', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: currentSession.id, student_id: parseInt(stEligible.value, 10) }),
        });
        if (r.ok) { refreshStudents(); }
        else { const err = await r.json(); if (stMessage){ stMessage.textContent = 'Ошибка: ' + (err.detail || r.status); stMessage.className = 'message error'; } }
    } catch(e) { if (stMessage){ stMessage.textContent = 'Сетевая ошибка: ' + e.message; stMessage.className = 'message error'; } }
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

onEl(dayInput, 'change', loadGrid);
if (dayInput) dayInput.value = new Date().toISOString().slice(0, 10);
(async function () {
    await initPerms();
    await loadDicts();
    await loadGrid();
})();
