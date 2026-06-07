Auth.requireRole(['methodist', 'branch_admin', 'admin']);

const QUANTS = 10;
const dayInput = document.getElementById('day');
const gridBody = document.getElementById('grid-body');

const overlay = document.getElementById('overlay');
const lessonSel = document.getElementById('m_lesson');
const roomSel = document.getElementById('m_room');
const modalMessage = document.getElementById('modal-message');

const evOverlay = document.getElementById('ev-overlay');
const evEventSel = document.getElementById('ev_event');
const evMessage = document.getElementById('ev-message');

const stOverlay = document.getElementById('students-overlay');
const stTitle = document.getElementById('st-title');
const stInfo = document.getElementById('st-info');
const stCapacity = document.getElementById('st-capacity');
const stList = document.getElementById('st-list');
const stEligible = document.getElementById('st-eligible');
const stMessage = document.getElementById('st-message');

const exOverlay = document.getElementById('ex-overlay');
const exExamSel = document.getElementById('ex_exam');
const exRoomSel = document.getElementById('ex_room');
const exEligible = document.getElementById('ex_eligible');
const exPending = document.getElementById('ex_pending');
const exMessage = document.getElementById('ex-message');

const exsOverlay = document.getElementById('exs-overlay');
const exsTitle = document.getElementById('exs-title');
const exsInfo = document.getElementById('exs-info');
const exsList = document.getElementById('exs-list');
const exsEligible = document.getElementById('exs-eligible');
const exsMessage = document.getElementById('exs-message');

const LVL = { beginner: 'Начинающий', intermediate: 'Средний', advanced: 'Продвинутый' };
const EXRES = { pending: 'Ожидает', passed: 'Сдал', failed: 'Не сдал' };

let lessonsCache = [];
let eventsCache = [];
let roomsCache = [];
let examsCache = [];
let studentsCache = [];
let currentEntries = [];
let currentQuant = null;
let currentSession = null;
let currentExamSession = null;
let examPending = [];
let canAddSession = false;
let canAddEvent = false;
let canAddExam = false;

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
        canAddEvent = role === 'methodist' || role === 'branch_admin' || role === 'admin' || su;
        canAddExam = role === 'methodist' || role === 'branch_admin' || role === 'admin' || su;
    } catch (e) {}
}

async function loadDicts() {
    try {
        const [lr, rr] = await Promise.all([
            Auth.apiFetch('/api/lessons'),
            Auth.apiFetch('/api/rooms?only_active=true'),
        ]);
        lessonsCache = await lr.json(); if (!Array.isArray(lessonsCache)) lessonsCache = [];
        roomsCache = await rr.json(); if (!Array.isArray(roomsCache)) roomsCache = [];
        if (lessonSel) lessonSel.innerHTML = lessonsCache.map(l => {
            const disc = l.discipline ? l.discipline.name : '—';
            const t = teacherName(l.teacher);
            return `<option value="${l.id}">${esc(disc)}${t ? ' — ' + esc(t) : ''}${l.lesson_type ? ' ('+esc(l.lesson_type)+')' : ''}</option>`;
        }).join('') || '<option value="">Нет занятий — создайте сначала</option>';
        const roomOpts = '<option value="">— без кабинета —</option>' +
            roomsCache.map(r => `<option value="${r.id}">${esc(r.name)}${r.branch ? ' ('+esc(r.branch)+')' : ''}</option>`).join('');
        if (roomSel) roomSel.innerHTML = roomOpts;
        if (exRoomSel) exRoomSel.innerHTML = roomOpts;
    } catch(e) {}
}

async function loadStudentsCache() {
    try {
        const r = await Auth.apiFetch('/api/leads?is_student=true');
        const d = await r.json();
        studentsCache = Array.isArray(d) ? d : [];
    } catch(e) { studentsCache = []; }
}
function studentLabel(s){ return s.student_full_name || s.contact_full_name || ('Ученик №' + s.id); }

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
                    <div style="font-weight:600;">Концерт: ${esc(ev.title || '')}</div>
                    <div style="color:#555;">${ev.description ? esc(ev.description) : ''}</div>
                </div>`;
            }
            if (e.entity_type === 'exam') {
                const ex = e.exam || {};
                const stu = ex.students || [];
                return `<div class="exam-chip" data-entry="${e.id}" title="Открыть проведение" style="background:#eee7ff; border-radius:8px; padding:8px 10px; margin-bottom:6px; font-size:13px; position:relative; cursor:pointer;">
                    <button class="del" data-id="${e.id}" title="Убрать из расписания" style="position:absolute; top:4px; right:8px; cursor:pointer; color:#8c1f1f; border:none; background:none; font-size:14px;">&times;</button>
                    <div style="font-weight:600;">Экзамен: ${esc(ex.exam_type || '')}${ex.discipline_name ? ' · ' + esc(ex.discipline_name) : ''}</div>
                    <div style="color:#555;">${ex.commission_name ? esc(ex.commission_name) + ' · ' : ''}${stu.length} уч.</div>
                </div>`;
            }
            const s = e.session;
            const disc = s && s.lesson && s.lesson.discipline ? s.lesson.discipline.name : '—';
            const t = s && s.lesson ? teacherName(s.lesson.teacher) : '';
            const room = s && s.room ? s.room.name : 'без кабинета';
            return `<div class="sess" data-entry="${e.id}">
                <button class="del" data-id="${e.id}" title="Убрать из расписания">&times;</button>
                <div class="disc">Занятие: ${esc(disc)}</div>
                <div class="meta">${esc(t)} · ${esc(room)}</div>
            </div>`;
        }).join('');

        const addButtons =
            (canAddSession ? `<button class="add-btn add-session" data-quant="${q}">+ Занятие</button>` : '') +
            (canAddEvent ? `<button class="add-btn add-event" data-quant="${q}" style="margin-top:6px; color:#8a5b00;">+ Концерт</button>` : '') +
            (canAddExam ? `<button class="add-btn add-exam" data-quant="${q}" style="margin-top:6px; color:#5a3fb0;">+ Экзамен</button>` : '');

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
    document.querySelectorAll('.add-exam').forEach(b =>
        b.addEventListener('click', () => openExamModal(parseInt(b.dataset.quant, 10))));
    document.querySelectorAll('.del').forEach(b =>
        b.addEventListener('click', (ev) => { ev.stopPropagation(); removeEntry(b.dataset.id); }));
    document.querySelectorAll('.sess').forEach(card =>
        card.addEventListener('click', () => {
            const entry = currentEntries.find(x => String(x.id) === card.dataset.entry);
            if (entry && entry.session) openStudentsModal(entry.session);
        }));
    document.querySelectorAll('.exam-chip').forEach(card =>
        card.addEventListener('click', () => {
            const entry = currentEntries.find(x => String(x.id) === card.dataset.entry);
            if (entry && entry.exam) openExamStudentsModal(entry.exam);
        }));
}

// занятие
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
    const payload = { day: dayInput.value, quant: currentQuant, lesson_id: parseInt(lessonSel.value, 10),
        room_id: roomSel && roomSel.value ? parseInt(roomSel.value, 10) : null };
    try {
        const r = await Auth.apiFetch('/api/schedule/add-session', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        if (r.ok) { closeAddModal(); loadGrid(); }
        else { const err = await r.json(); if (modalMessage){ modalMessage.textContent = 'Ошибка: ' + (err.detail || r.status); modalMessage.className = 'message error'; } }
    } catch(e) { if (modalMessage){ modalMessage.textContent = 'Сетевая ошибка: ' + e.message; modalMessage.className = 'message error'; } }
});

// концерт
async function loadEventsForSelect() {
    try { const r = await Auth.apiFetch('/api/events'); const d = await r.json(); eventsCache = Array.isArray(d) ? d : []; }
    catch(e) { eventsCache = []; }
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
        const r = await Auth.apiFetch('/api/schedule/place-event', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        if (r.ok) { closeEventModal(); loadGrid(); }
        else { const err = await r.json(); if (evMessage){ evMessage.textContent = 'Ошибка: ' + (err.detail || r.status); evMessage.className = 'message error'; } }
    } catch(e) { if (evMessage){ evMessage.textContent = 'Сетевая ошибка: ' + e.message; evMessage.className = 'message error'; } }
});

// экзамен: назначение
async function loadExamsForSelect() {
    try { const r = await Auth.apiFetch('/api/exams'); const d = await r.json(); examsCache = Array.isArray(d) ? d : []; }
    catch(e) { examsCache = []; }
    if (exExamSel) exExamSel.innerHTML = examsCache.length
        ? examsCache.map(x => {
            const label = `${x.discipline_name || '—'}${x.exam_type ? ' · ' + x.exam_type : ''}${x.commission_name ? ' · ' + x.commission_name : ''}`;
            return `<option value="${x.id}">${esc(label)}</option>`;
        }).join('')
        : '<option value="">Сначала создайте экзамен на странице «Экзамены»</option>';
}
function renderExamPending() {
    if (!exPending) return;
    exPending.innerHTML = examPending.map((s, i) =>
        `<span style="display:inline-flex; align-items:center; gap:6px; padding:4px 8px; border-radius:999px; background:#f0f0f3; font-size:12px;">
            ${esc(s.name)} <span data-rm="${i}" style="cursor:pointer; color:#86868b; font-weight:700;">×</span></span>`).join('');
}
function renderExamEligible() {
    if (!exEligible) return;
    const chosen = new Set(examPending.map(s => s.id));
    const list = studentsCache.filter(s => !chosen.has(s.id));
    exEligible.innerHTML = list.length
        ? '<option value="">— выберите ученика —</option>' + list.map(s => `<option value="${s.id}">${esc(studentLabel(s))}</option>`).join('')
        : '<option value="">Нет доступных учеников</option>';
}
async function openExamModal(quant) {
    currentQuant = quant; examPending = [];
    if (exMessage) exMessage.classList.add('hidden');
    const tt = document.getElementById('ex-title-h');
    if (tt) tt.textContent = `Назначить экзамен — квант ${quant} (${quantTime(quant)})`;
    await loadExamsForSelect();
    if (!studentsCache.length) await loadStudentsCache();
    renderExamPending(); renderExamEligible();
    if (exOverlay) exOverlay.classList.add('show');
}
function closeExamModal() { if (exOverlay) exOverlay.classList.remove('show'); currentQuant = null; examPending = []; }
on('ex_cancel', 'click', closeExamModal);
onEl(exOverlay, 'click', e => { if (e.target === exOverlay) closeExamModal(); });
on('ex_add', 'click', () => {
    if (!exEligible || !exEligible.value) return;
    const id = parseInt(exEligible.value, 10);
    if (examPending.some(s => s.id === id)) return;
    const s = studentsCache.find(x => x.id === id);
    examPending.push({ id, name: s ? studentLabel(s) : ('Ученик №' + id) });
    renderExamPending(); renderExamEligible();
});
onEl(exPending, 'click', e => {
    const x = e.target.closest('[data-rm]'); if (!x) return;
    examPending.splice(parseInt(x.dataset.rm, 10), 1);
    renderExamPending(); renderExamEligible();
});
on('ex_save', 'click', async () => {
    if (exMessage) exMessage.classList.add('hidden');
    if (!exExamSel || !exExamSel.value) { if (exMessage){ exMessage.textContent = 'Выберите экзамен'; exMessage.className = 'message error'; } return; }
    const payload = { day: dayInput.value, quant: currentQuant, exam_id: parseInt(exExamSel.value, 10),
        room_id: exRoomSel && exRoomSel.value ? parseInt(exRoomSel.value, 10) : null,
        student_ids: examPending.map(s => s.id) };
    try {
        const r = await Auth.apiFetch('/api/schedule/add-exam', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        if (r.ok) { closeExamModal(); loadGrid(); }
        else { const err = await r.json(); if (exMessage){ exMessage.textContent = 'Ошибка: ' + (err.detail || r.status); exMessage.className = 'message error'; } }
    } catch(e) { if (exMessage){ exMessage.textContent = 'Сетевая ошибка: ' + e.message; exMessage.className = 'message error'; } }
});

// экзамен: проведение
function lvlOptions(sel){ return '<option value="">— уровень —</option>' + ['beginner','intermediate','advanced'].map(v => `<option value="${v}"${sel===v?' selected':''}>${LVL[v]}</option>`).join(''); }
function resOptions(sel){ return ['pending','passed','failed'].map(v => `<option value="${v}"${sel===v?' selected':''}>${EXRES[v]}</option>`).join(''); }

function openExamStudentsModal(examSession) {
    currentExamSession = examSession;
    if (exsMessage) exsMessage.classList.add('hidden');
    if (exsTitle) exsTitle.textContent = `Экзамен: ${examSession.exam_type || ''}${examSession.discipline_name ? ' · ' + examSession.discipline_name : ''}`;
    if (exsInfo) exsInfo.textContent = `Комиссия: ${examSession.commission_name || '—'} · Кабинет: ${examSession.room_name || 'без кабинета'} · Статус: ${examSession.status || ''}`;
    if (exsOverlay) exsOverlay.classList.add('show');
    refreshExamStudents();
}
function closeExamStudentsModal() { if (exsOverlay) exsOverlay.classList.remove('show'); currentExamSession = null; }
on('exs-close', 'click', closeExamStudentsModal);
onEl(exsOverlay, 'click', e => { if (e.target === exsOverlay) closeExamStudentsModal(); });

async function refreshExamStudents() {
    if (!currentExamSession) return;
    const sid = currentExamSession.id;
    let students = [];
    try { const r = await Auth.apiFetch('/api/exam-sessions/' + sid + '/students'); students = await r.json(); } catch(e) {}
    if (!Array.isArray(students)) students = [];

    if (exsList) exsList.innerHTML = students.length ? students.map(s => `
        <div class="exs-row" data-ess="${s.id}" style="border-bottom:1px solid #eee; padding:8px 0;">
            <div style="font-weight:600;">${esc(s.student_name || ('Ученик №' + s.student_id))}</div>
            <div style="display:flex; gap:6px; margin-top:6px; flex-wrap:wrap; align-items:center;">
                <select class="exs-result" style="width:auto;">${resOptions(s.result)}</select>
                <select class="exs-level" style="width:auto;">${lvlOptions(s.result_level)}</select>
                <input type="number" class="exs-score" placeholder="балл" value="${s.score != null ? s.score : ''}" style="width:70px;">
                <input type="text" class="exs-comment" placeholder="комментарий" value="${esc(s.comment || '')}" style="flex:1; min-width:120px;">
                <button class="btn-primary exs-save" data-ess="${s.id}" style="padding:4px 10px;">Сохранить</button>
                <button class="btn-ghost exs-rm" data-ess="${s.id}" style="padding:4px 10px;">Убрать</button>
            </div>
        </div>`).join('') : '<div style="color:#aaa; padding:6px 0;">Ученики не назначены</div>';

    if (!studentsCache.length) await loadStudentsCache();
    const enrolledIds = new Set(students.map(s => s.student_id));
    const cand = studentsCache.filter(s => !enrolledIds.has(s.id));
    if (exsEligible) exsEligible.innerHTML = cand.length
        ? '<option value="">— выберите ученика —</option>' + cand.map(s => `<option value="${s.id}">${esc(studentLabel(s))}</option>`).join('')
        : '<option value="">Нет доступных учеников</option>';
}

onEl(exsList, 'click', async (e) => {
    const saveBtn = e.target.closest('.exs-save');
    const rmBtn = e.target.closest('.exs-rm');
    if (saveBtn) {
        const ess = saveBtn.dataset.ess;
        const row = saveBtn.closest('.exs-row');
        const scoreRaw = row.querySelector('.exs-score').value;
        const payload = {
            result: row.querySelector('.exs-result').value,
            result_level: row.querySelector('.exs-level').value || null,
            score: scoreRaw === '' ? null : parseInt(scoreRaw, 10),
            comment: row.querySelector('.exs-comment').value || null,
            apply_level: true,
        };
        if (exsMessage) exsMessage.classList.add('hidden');
        try {
            const r = await Auth.apiFetch('/api/exam-session-students/' + ess, { method:'PATCH', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
            if (r.ok) { if (exsMessage){ exsMessage.textContent = 'Сохранено'; exsMessage.className = 'message success'; } }
            else { const err = await r.json(); if (exsMessage){ exsMessage.textContent = 'Ошибка: ' + (err.detail || r.status); exsMessage.className = 'message error'; } }
        } catch(err) { if (exsMessage){ exsMessage.textContent = 'Сетевая ошибка: ' + err.message; exsMessage.className = 'message error'; } }
        return;
    }
    if (rmBtn) {
        try { await Auth.apiFetch('/api/exam-session-students/' + rmBtn.dataset.ess, { method:'DELETE' }); refreshExamStudents(); loadGrid(); }
        catch(err) { if (exsMessage){ exsMessage.textContent = 'Ошибка: ' + err.message; exsMessage.className = 'message error'; } }
    }
});
on('exs-add', 'click', async () => {
    if (exsMessage) exsMessage.classList.add('hidden');
    if (!exsEligible || !exsEligible.value) { if (exsMessage){ exsMessage.textContent = 'Выберите ученика'; exsMessage.className = 'message error'; } return; }
    try {
        const r = await Auth.apiFetch('/api/exam-sessions/' + currentExamSession.id + '/students', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ student_id: parseInt(exsEligible.value, 10) }) });
        if (r.ok) { refreshExamStudents(); loadGrid(); }
        else { const err = await r.json(); if (exsMessage){ exsMessage.textContent = 'Ошибка: ' + (err.detail || r.status); exsMessage.className = 'message error'; } }
    } catch(e) { if (exsMessage){ exsMessage.textContent = 'Сетевая ошибка: ' + e.message; exsMessage.className = 'message error'; } }
});

async function removeEntry(id) {
    try { await Auth.apiFetch('/api/schedule/' + id, { method:'DELETE' }); loadGrid(); }
    catch(e) { alert('Ошибка: ' + e.message); }
}

// ученики занятия
function openStudentsModal(session) {
    currentSession = session;
    if (stMessage) stMessage.classList.add('hidden');
    const disc = session.lesson && session.lesson.discipline ? session.lesson.discipline.name : '—';
    const room = session.room ? session.room.name : 'без кабинета';
    const branch = session.room && session.room.branch ? session.room.branch : '—';
    if (stTitle) stTitle.textContent = `Ученики: ${disc}`;
    const lvl = session.lesson && session.lesson.level ? (LVL[session.lesson.level] || session.lesson.level) : 'любой';
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
    try { const r = await Auth.apiFetch('/api/session-students?session_id=' + sid); enrolled = await r.json(); } catch(e) {}
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
    document.querySelectorAll('.att').forEach(c => c.addEventListener('change', () => setAttended(c.dataset.id, c.checked)));
    if (stList) stList.querySelectorAll('.btn-no').forEach(b => b.addEventListener('click', () => unenroll(b.dataset.id)));
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
        const r = await Auth.apiFetch('/api/session-students', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ session_id: currentSession.id, student_id: parseInt(stEligible.value, 10) }) });
        if (r.ok) { refreshStudents(); }
        else { const err = await r.json(); if (stMessage){ stMessage.textContent = 'Ошибка: ' + (err.detail || r.status); stMessage.className = 'message error'; } }
    } catch(e) { if (stMessage){ stMessage.textContent = 'Сетевая ошибка: ' + e.message; stMessage.className = 'message error'; } }
});
async function setAttended(id, attended) {
    try { await Auth.apiFetch('/api/session-students/' + id, { method:'PATCH', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ attended }) }); }
    catch(e) { alert('Ошибка: ' + e.message); }
}
async function unenroll(id) {
    try { await Auth.apiFetch('/api/session-students/' + id, { method:'DELETE' }); refreshStudents(); }
    catch(e) { alert('Ошибка: ' + e.message); }
}

onEl(dayInput, 'change', loadGrid);
if (dayInput) dayInput.value = new Date().toISOString().slice(0, 10);
(async function () {
    await initPerms();
    await loadDicts();
    await loadStudentsCache();
    await loadGrid();
})();
