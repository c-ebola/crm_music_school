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
// День занятия берём из ДАТЫ session_date (без времени), чтобы не было сдвига по таймзоне
function dayIndexOf(iso){
    const [y,m,d] = iso.slice(0,10).split('-').map(Number);
    return (new Date(y, m-1, d).getDay() + 6) % 7;
}

async function init(){
    const r = await fetch('/api/auth/me', { headers: authHeaders });
    if (r.status === 401){ localStorage.removeItem('token'); window.location.href='/login'; return; }
    const me = await r.json();
    whoEl.textContent = `${me.full_name} (${me.role.name})`;
    teacherId = me.id;

    await maybeSetupTeacherPicker(me);   // для админа — выбор любого преподавателя
    bindNav();
    loadWeek();
}

// Селектор преподавателей показываем только тем, у кого есть доступ к /api/users (админ).
async function maybeSetupTeacherPicker(me){
    try {
        const r = await fetch('/api/users', { headers: authHeaders });
        if (!r.ok) return;                       // 403 у обычного преподавателя — просто скрыт
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
        const r = await fetch(`/api/schedule/week?week_start=${ws}&teacher_id=${teacherId}`,
                              { headers: authHeaders });
        const data = await r.json();
        entries = Array.isArray(data) ? data : [];   // если пришла ошибка — не падаем
    } catch(e){ entries = []; }

    emptyEl.classList.toggle('hidden', entries.length > 0);

    const cells = {};
    let maxQuant = DEFAULT_QUANTS;
    entries.forEach(e => {
        const s = e.session; if (!s) return;
        const q = e.quant; maxQuant = Math.max(maxQuant, q);
        const day = dayIndexOf(e.date);          // < день из расписания, не из сессии
        if (day < 0 || day > 6) return;
        (cells[q] = cells[q] || {});
        (cells[q][day] = cells[q][day] || []).push(s);
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

function chip(s){
    const disc = s.lesson && s.lesson.discipline ? s.lesson.discipline.name : '—';
    const room = s.room ? s.room.name : 'без кабинета';
    const type = s.lesson && s.lesson.lesson_type ? s.lesson.lesson_type : '';
    const st = STATUS[s.status] || { label: s.status || '', cls: '' };
    return `<div class="lesson-chip ${st.cls}">
        <div class="disc">${esc(disc)}</div>
        <div class="meta">${esc(room)}${type ? ' · ' + esc(type) : ''}</div>
        ${st.label ? `<div class="meta">${esc(st.label)}</div>` : ''}
    </div>`;
}

init();