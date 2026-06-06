Auth.requireRole(['teacher', 'admin']);

let me = null;
let isAdmin = false;
let viewTeacherId = null;       // чьё расписание смотрим (учитель — своё; админ — выбранного)
let daySessions = [];
let current = null;             // выбранная сессия
let curStudents = [];

const FMT = { individual:'Индивидуальное', group:'Групповое', online:'Онлайн' };
const LVL = { beginner:'Начинающий', intermediate:'Средний', advanced:'Продвинутый' };
const ST_LABEL = { scheduled:'Запланировано', completed:'Проведено', cancelled:'Отменено' };

const $ = id => document.getElementById(id);
function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function pad(n){ return String(n).padStart(2,'0'); }
function isoDate(d){ return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`; }
function fmtRu(iso){ if(!iso) return ''; const d=new Date(iso); return `${pad(d.getDate())}.${pad(d.getMonth()+1)}.${d.getFullYear()}`; }
function teacherName(t){ return t ? [t.last_name, t.first_name].filter(Boolean).join(' ') : ''; }
function quantTime(q){
    const s = 9*60 + (q-1)*60, e = s + 45;
    return `${pad(Math.floor(s/60))}:${pad(s%60)}–${pad(Math.floor(e/60))}:${pad(e%60)}`;
}

async function init(){
    const r = await Auth.apiFetch('/api/auth/me');
    if (r.status === 401){ window.location.href='/login'; return; }
    me = await r.json();
    isAdmin = (me.role && me.role.code === 'admin') || me.is_superuser;
    viewTeacherId = me.id;
    $('who').textContent = isAdmin ? 'Просмотр занятий' : `${me.full_name} · отметка статусов и посещаемости`;

    $('day').value = isoDate(new Date());
    if (isAdmin) await setupTeacherPicker();

    $('day').addEventListener('change', loadDay);
    $('prev').addEventListener('click', () => shiftDay(-1));
    $('next').addEventListener('click', () => shiftDay(1));
    $('today-btn').addEventListener('click', () => { $('day').value = isoDate(new Date()); loadDay(); });

    $('detail').addEventListener('click', onDetailClick);
    $('mark-all').addEventListener('click', markAll);

    await loadDay();
}

async function setupTeacherPicker(){
    try {
        const users = await (await Auth.apiFetch('/api/users')).json();
        const teachers = (Array.isArray(users) ? users : []).filter(u => u.role && u.role.code === 'teacher');
        const sel = $('teacher-sel');
        sel.innerHTML = '<option value="">Все преподаватели</option>' +
            teachers.map(u => `<option value="${u.id}">${esc(u.full_name)}</option>`).join('');
        sel.classList.remove('hidden');
        sel.addEventListener('change', () => { viewTeacherId = sel.value ? Number(sel.value) : null; loadDay(); });
        viewTeacherId = null; // админ по умолчанию видит все
    } catch(e){ /* нет прав на список — оставляем своё */ }
}

function shiftDay(delta){
    const d = new Date($('day').value || new Date());
    d.setDate(d.getDate() + delta);
    $('day').value = isoDate(d);
    loadDay();
}

async function loadDay(){
    current = null;
    $('detail').classList.add('hidden');
    $('placeholder').classList.remove('hidden');
    $('sess-list').innerHTML = '<div class="empty">Загрузка…</div>';

    const day = $('day').value;
    let entries = [];
    try {
        const r = await Auth.apiFetch('/api/schedule?day=' + day);
        entries = await r.json();
    } catch(e){ entries = []; }
    if (!Array.isArray(entries)) entries = [];

    daySessions = entries
        .filter(e => e.entity_type === 'session' && e.session)
        .map(e => Object.assign({}, e.session, { _quant: e.quant, _date: e.date }))
        .filter(s => {
            if (viewTeacherId == null) return true;                 // админ: все
            return s.lesson && s.lesson.teacher && s.lesson.teacher.id === viewTeacherId;
        })
        .sort((a, b) => a._quant - b._quant);

    renderList();
}

function renderList(){
    if (!daySessions.length){
        $('sess-list').innerHTML = '<div class="empty">На этот день занятий нет.</div>';
        return;
    }
    $('sess-list').innerHTML = daySessions.map(s => {
        const disc = s.lesson && s.lesson.discipline ? s.lesson.discipline.name : '—';
        const room = s.room ? s.room.name : 'без кабинета';
        const st = s.status || 'scheduled';
        return `<div class="sess-item ${current && current.id === s.id ? 'active' : ''}" data-id="${s.id}">
            <div class="sess-time">${quantTime(s._quant)} <span class="badge ${st}">${esc(ST_LABEL[st]||st)}</span></div>
            <div class="sess-disc">${esc(disc)}</div>
            <div class="sess-room">${esc(room)}</div>
        </div>`;
    }).join('');

    $('sess-list').querySelectorAll('.sess-item').forEach(el => {
        el.addEventListener('click', () => selectSession(parseInt(el.dataset.id, 10)));
    });
}

async function selectSession(id){
    current = daySessions.find(s => s.id === id) || null;
    renderList();
    if (!current) return;

    $('placeholder').classList.add('hidden');
    $('detail').classList.remove('hidden');
    $('status-hint').textContent = '';

    const l = current.lesson || {};
    const disc = l.discipline ? l.discipline.name : '—';
    const fmt = l.lesson_type ? (FMT[l.lesson_type] || l.lesson_type) : '';
    const lvl = l.level ? (LVL[l.level] || l.level) : '';
    const room = current.room ? current.room.name : 'без кабинета';
    const tch = teacherName(l.teacher);

    $('d-title').textContent = [disc, fmt, lvl].filter(Boolean).join(' · ');
    $('d-sub').textContent = [room, `${quantTime(current._quant)}`, fmtRu(current._date), tch]
        .filter(Boolean).join(' · ');

    paintStatus(current.status || 'scheduled');
    await loadStudents();
}

function paintStatus(status){
    document.querySelectorAll('.st-card').forEach(c => {
        c.className = 'st-card' + (c.dataset.status === status ? ' sel-' + status : '');
    });
}

async function onDetailClick(e){
    const card = e.target.closest('.st-card');
    if (!card || !current) return;
    const status = card.dataset.status;
    if (status === current.status) return;

    paintStatus(status);
    $('status-hint').textContent = 'Сохранение…';
    $('status-hint').className = 'save-hint';
    try {
        const r = await Auth.apiFetch('/api/sessions/' + current.id, {
            method:'PATCH', headers:{ 'Content-Type':'application/json' },
            body: JSON.stringify({ status }),
        });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const data = await r.json();
        current.status = data.status;
        const i = daySessions.findIndex(s => s.id === current.id);
        if (i >= 0) daySessions[i].status = data.status;
        renderList();
        $('status-hint').textContent = 'Статус сохранён: ' + (ST_LABEL[data.status] || data.status);
        $('status-hint').className = 'save-hint ok';
    } catch(err){
        paintStatus(current.status || 'scheduled');
        $('status-hint').textContent = 'Не удалось сохранить статус';
        $('status-hint').className = 'save-hint err';
    }
}

async function loadStudents(){
    curStudents = [];
    $('stud-list').innerHTML = '<div class="empty">Загрузка…</div>';
    try {
        const r = await Auth.apiFetch('/api/session-students?session_id=' + current.id);
        curStudents = await r.json();
    } catch(e){ curStudents = []; }
    if (!Array.isArray(curStudents)) curStudents = [];
    renderStudents();
}

function renderStudents(){
    const max = current.lesson ? current.lesson.max_students : null;
    $('cap').textContent = `Записано: ${curStudents.length}${max != null ? ' из ' + max : ''}`;

    if (!curStudents.length){
        $('stud-list').innerHTML = '<div class="empty">Никто не записан на это занятие.</div>';
        $('mark-all').classList.add('hidden');
        return;
    }
    $('mark-all').classList.remove('hidden');

    $('stud-list').innerHTML = curStudents.map(s => {
        const name = s.student_name || ('Ученик №' + s.student_id);
        const note = s.attended
            ? 'Пришёл · занятие списано с абонемента'
            : 'Не пришёл · списания нет';
        return `<div class="stud" data-id="${s.id}">
            <div class="name">${esc(name)}</div>
            <div class="sub-note">${esc(note)}</div>
            <div class="att-row">
                <button class="att-btn came ${s.attended ? 'on' : ''}" data-id="${s.id}" data-att="1">Пришёл</button>
                <button class="att-btn miss ${s.attended ? '' : 'on'}" data-id="${s.id}" data-att="0">Не пришёл</button>
            </div>
            <div class="stud-msg hidden" data-msg="${s.id}"></div>
        </div>`;
    }).join('');

    $('stud-list').querySelectorAll('.att-btn').forEach(b => {
        b.addEventListener('click', () => setAttended(parseInt(b.dataset.id, 10), b.dataset.att === '1'));
    });
}

async function setAttended(ssId, attended){
    const msg = document.querySelector(`[data-msg="${ssId}"]`);
    if (msg){ msg.classList.add('hidden'); }
    try {
        const r = await Auth.apiFetch('/api/session-students/' + ssId, {
            method:'PATCH', headers:{ 'Content-Type':'application/json' },
            body: JSON.stringify({ attended }),
        });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const data = await r.json();
        const i = curStudents.findIndex(s => s.id === ssId);
        if (i >= 0) curStudents[i] = data;
        renderStudents();
    } catch(err){
        if (msg){ msg.textContent = 'Ошибка сохранения'; msg.className = 'stud-msg err'; msg.classList.remove('hidden'); }
    }
}

async function markAll(){
    for (const s of curStudents){
        if (!s.attended) await setAttended(s.id, true);
    }
}

init();
