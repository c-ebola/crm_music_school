Auth.requireRole(['teacher', 'methodist', 'branch_admin', 'admin']);

const DEFAULT_QUANTS = 11;          // 9:00 … 19:45
const DOW = ['Пн','Вт','Ср','Чт','Пт','Сб','Вс'];
const style = document.createElement('style');

style.textContent = `
  .week-card {
    max-width: 1200px;
    width: 100%;
    overflow-x: auto;
  }

  .week-grid {
    width: 100%;
    min-width: 1000px;
    table-layout: fixed;
  }

  .week-grid .qtime {
    width: 120px;
    min-width: 120px;
    white-space: nowrap;
    font-size: 13px;
  }

  .week-grid th,
  .week-grid td {
    height: 46px;
    padding: 8px 10px;
  }
`;

document.head.appendChild(style);

const token = localStorage.getItem('token');
if (!token) window.location.href = '/login';
const authHeaders = { 'Authorization': 'Bearer ' + token };

const headEl = document.getElementById('grid-head');
const bodyEl = document.getElementById('grid-body');
const rangeEl = document.getElementById('range');
const whoEl = document.getElementById('who');
const emptyEl = document.getElementById('empty');
const teacherSel = document.getElementById('teacher-sel');

let currentMonday = mondayOf(new Date());
let teacherId = null;

const STATUS = {
    scheduled: { label: 'запланировано', cls: '' },
    completed: { label: 'проведено',     cls: 'done' },
    done:      { label: 'проведено',     cls: 'done' },
    cancelled: { label: 'отменено',      cls: 'cancelled' },
    canceled:  { label: 'отменено',      cls: 'cancelled' },
};

function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function pad(n){ return String(n).padStart(2,'0'); }
function isoDate(d){ return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`; }
function fmt(d){ return `${pad(d.getDate())}.${pad(d.getMonth()+1)}`; }
function teacherName(t){ return t ? [t.last_name, t.first_name].filter(Boolean).join(' ') : ''; }

function mondayOf(date){
    const d = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    const shift = (d.getDay() + 6) % 7;          // Пн = 0
    d.setDate(d.getDate() - shift);
    return d;
}
function quantTime(q){
    const s = 9*60 + (q-1)*60, e = s + 45;
    return `${pad(Math.floor(s/60))}:${pad(s%60)}–${pad(Math.floor(e/60))}:${pad(e%60)}`;
}
function dayIndexOf(iso){
    const [y,m,d] = iso.slice(0,10).split('-').map(Number);
    return (new Date(y, m-1, d).getDay() + 6) % 7;
}

async function init(){
    const r = await Auth.apiFetch('/api/auth/me', { headers: authHeaders });
    if (r.status === 401){ localStorage.removeItem('token'); window.location.href='/login'; return; }
    const me = await r.json();
    whoEl.textContent = `${me.full_name} (${me.role.name})`;
    teacherId = me.id;

    await maybeSetupTeacherPicker(me);
    bindNav();
    loadWeek();
}

async function maybeSetupTeacherPicker(me){
    const isAdmin = (me.role && me.role.code === 'admin') || me.is_superuser;
    if (!isAdmin) return;
    try {
        const r = await Auth.apiFetch('/api/users', { headers: authHeaders });
        if (!r.ok) return;
        const users = await r.json();
        const teachers = users.filter(u => u.role && u.role.code === 'teacher');
        if (!teachers.length) return;
        teacherSel.innerHTML = teachers
            .map(u => `<option value="${u.id}">${esc(u.full_name)}</option>`).join('');
        if (teachers.some(t => t.id === me.id)) teacherSel.value = String(me.id);
        else teacherId = Number(teacherSel.value);
        teacherSel.classList.remove('hidden');
        teacherSel.addEventListener('change', () => { teacherId = Number(teacherSel.value); loadWeek(); });
    } catch(e){ /* нет прав — оставляем своё расписание */ }
}

function bindNav(){
    document.getElementById('prev').onclick = () => { currentMonday.setDate(currentMonday.getDate()-7); loadWeek(); };
    document.getElementById('next').onclick = () => { currentMonday.setDate(currentMonday.getDate()+7); loadWeek(); };
    document.getElementById('today-btn').onclick = () => { currentMonday = mondayOf(new Date()); loadWeek(); };
}

function buildHead(){
    const todayIso = isoDate(new Date());
    let html = '<th class="qtime">Время</th>';
    for (let i = 0; i < 7; i++){
        const d = new Date(currentMonday); d.setDate(d.getDate()+i);
        const today = isoDate(d) === todayIso ? ' today' : '';
        html += `<th class="day-h${today}"><div class="dow">${DOW[i]}</div><div class="date">${fmt(d)}</div></th>`;
    }
    headEl.innerHTML = html;
}

async function loadWeek(){
    const ws = isoDate(currentMonday);
    const we = new Date(currentMonday); we.setDate(we.getDate()+6);
    rangeEl.textContent = `${fmt(currentMonday)} – ${fmt(we)} ${we.getFullYear()}`;
    buildHead();

    let entries = [];
    try {
        const r = await Auth.apiFetch(`/api/schedule/week?week_start=${ws}&teacher_id=${teacherId}`,
                              { headers: authHeaders });
        const data = await r.json();
        entries = Array.isArray(data) ? data : [];
    } catch(e){ entries = []; }

    emptyEl.classList.toggle('hidden', entries.length > 0);

    const cells = {};
    let maxQuant = DEFAULT_QUANTS;
    entries.forEach(e => {
        let item = null;
        if (e.entity_type === 'session' && e.session) item = { kind: 'session', data: e.session };
        else if (e.entity_type === 'exam' && e.exam) item = { kind: 'exam', data: e.exam };
        else if (e.entity_type === 'event' && e.event) item = { kind: 'event', data: e.event };
        if (!item) return;
        const q = e.quant; maxQuant = Math.max(maxQuant, q);
        const day = dayIndexOf(e.date);
        if (day < 0 || day > 6) return;
        (cells[q] = cells[q] || {});
        (cells[q][day] = cells[q][day] || []).push(item);
    });

    const todayIdx = (() => {
        const t = new Date(); const tm = mondayOf(t);
        return isoDate(tm) === isoDate(currentMonday) ? (t.getDay()+6)%7 : -1;
    })();

    let body = '';
    for (let q = 1; q <= maxQuant; q++){
        body += `<tr><td class="qtime">${quantTime(q)}</td>`;
        for (let day = 0; day < 7; day++){
            const td = day === todayIdx ? ' class="today"' : '';
            const items = (cells[q] && cells[q][day]) || [];
            body += `<td${td}>${items.map(chip).join('')}</td>`;
        }
        body += '</tr>';
    }
    bodyEl.innerHTML = body;
}

function chip(item){
    if (item.kind === 'event'){
        const ev = item.data;
        return `<div class="lesson-chip" style="background:#fdeecf;">
            <div class="disc">Концерт: ${esc(ev.title || '')}</div>
            ${ev.description ? `<div class="meta">${esc(ev.description)}</div>` : ''}
        </div>`;
    }
    if (item.kind === 'exam'){
        const ex = item.data;
        const st = STATUS[ex.status] || { label: ex.status || '', cls: '' };
        const meta = [ex.exam_type, ex.commission_name].filter(Boolean).join(' · ');
        return `<div class="lesson-chip ${st.cls}" style="background:#eee7ff;">
            <div class="disc">Экзамен: ${esc(ex.discipline_name || ex.exam_type || '')}</div>
            ${meta ? `<div class="meta">${esc(meta)}</div>` : ''}
            ${st.label ? `<div class="meta">${esc(st.label)}</div>` : ''}
        </div>`;
    }
    const s = item.data;
    const disc = s.lesson && s.lesson.discipline ? s.lesson.discipline.name : '—';
    const room = s.room ? s.room.name : 'без кабинета';
    const FMT = { individual:'Индивидуальное', group:'Групповое', online:'Онлайн' };
    const type = s.lesson && s.lesson.lesson_type ? (window.Labels ? Labels.lessonType(s.lesson.lesson_type) : (FMT[s.lesson.lesson_type] || s.lesson.lesson_type)) : '';
    const st = STATUS[s.status] || { label: s.status || '', cls: '' };
    return `<div class="lesson-chip ${st.cls}">
        <div class="disc">${esc(disc)}</div>
        <div class="meta">${esc(room)}${type ? ' · ' + esc(type) : ''}</div>
        ${st.label ? `<div class="meta">${esc(st.label)}</div>` : ''}
    </div>`;
}

init();
