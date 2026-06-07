Auth.requireRole(['student', 'admin']);

const SUB_STATUS = { active:'Активен', expired:'Истёк', used_up:'Занятия закончились', cancelled:'Отменён' };
const DOW_FULL = ['Понедельник','Вторник','Среда','Четверг','Пятница','Суббота','Воскресенье'];

const $ = id => document.getElementById(id);
function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function pad(n){ return String(n).padStart(2,'0'); }
function isoDate(d){ return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`; }
function mondayOf(d){ const x=new Date(d.getFullYear(),d.getMonth(),d.getDate()); x.setDate(x.getDate()-((x.getDay()+6)%7)); return x; }
function teacherName(t){ return t ? [t.last_name, t.first_name].filter(Boolean).join(' ') : ''; }
function quantTime(q){ const s=9*60+(q-1)*60, e=s+45; return `${pad(Math.floor(s/60))}:${pad(s%60)}–${pad(Math.floor(e/60))}:${pad(e%60)}`; }
function fmtRu(iso){ if(!iso) return ''; const d=new Date(iso); return `${pad(d.getDate())}.${pad(d.getMonth()+1)}.${d.getFullYear()}`; }

let schedMonday = mondayOf(new Date());

function showBlocker(text){
    $('cab').classList.add('hidden');
    $('blocker').classList.remove('hidden');
    $('blocker-text').textContent = text;
}

async function init(){
    const r = await Auth.apiFetch('/api/portal/me');
    if (r.status === 401){ window.location.href='/login'; return; }
    if (r.status === 403){ showBlocker('Этот раздел доступен только ученикам.'); $('who').textContent='—'; return; }
    if (!r.ok){ showBlocker('Не удалось загрузить кабинет.'); return; }
    const me = await r.json();
    $('who').textContent = me.name || 'Ученик';

    renderProfile(me);

    $('sch-prev').addEventListener('click', () => { schedMonday.setDate(schedMonday.getDate()-7); loadSchedule(); });
    $('sch-next').addEventListener('click', () => { schedMonday.setDate(schedMonday.getDate()+7); loadSchedule(); });
    $('sch-today').addEventListener('click', () => { schedMonday = mondayOf(new Date()); loadSchedule(); });

    await Promise.all([loadSubscription(), loadSchedule(), loadHomeworks()]);
}

function profileLine(label, value){
    return `<div class="profile-line"><span>${esc(label)}</span><b>${esc(value || '—')}</b></div>`;
}
function renderProfile(me){
    $('profile').innerHTML =
        profileLine('Имя', me.name) +
        profileLine('Дисциплина', me.discipline) +
        profileLine['Уровень', Labels.level(me.level)],
        profileLine['Формат занятий', Labels.lessonFormat(me.lesson_format)],
        profileLine('Возраст', me.age != null ? me.age + ' лет' : null) +
        profileLine('Филиал', me.branch) +
        profileLine('Классный руководитель', me.teacher);
}

// абонемент
async function loadSubscription(){
    let subs = [];
    try { subs = await (await Auth.apiFetch('/api/portal/subscriptions')).json(); }
    catch(e){ subs = []; }
    if (!Array.isArray(subs)) subs = [];

    if (!subs.length){
        $('sub-body').innerHTML = '<div class="sub-empty">Активного абонемента нет. Обратитесь к администратору филиала.</div>';
        return;
    }
    const cur = subs.find(s => s.status === 'active') || subs[0];
    const total = cur.lessons_total || 0;
    const used = cur.lessons_used || 0;
    const remain = cur.lessons_remaining != null ? cur.lessons_remaining : (total - used);
    const pct = total > 0 ? Math.round((used / total) * 100) : 0;

    $('sub-body').innerHTML = `
        <div class="sub-top">
            <div><div class="sub-remain">${remain}<small> / ${total} занятий осталось</small></div></div>
            <div class="sub-plan">${esc(cur.plan_name || 'Абонемент')}<br>
                <span class="pill2 ${esc(cur.status)}">${esc(SUB_STATUS[cur.status] || cur.status)}</span>
            </div>
        </div>
        <div class="sub-bar"><i style="width:${Math.min(pct,100)}%;"></i></div>
        <div class="sub-meta">
            <div>Использовано: <b>${used} из ${total}</b></div>
            <div>Действует до: <b>${fmtRu(cur.end_date)}</b></div>
            <div>Начало: <b>${fmtRu(cur.start_date)}</b></div>
        </div>
        ${subs.length > 1 ? `<div class="sub-meta" style="margin-top:10px;">Всего абонементов: <b>${subs.length}</b></div>` : ''}`;
}

// расписание (неделя с перелистыванием, показываем всё)
async function loadSchedule(){
    const ws = new Date(schedMonday);
    const we = new Date(schedMonday); we.setDate(we.getDate()+6);
    $('sch-range').textContent = `${pad(ws.getDate())}.${pad(ws.getMonth()+1)} – ${pad(we.getDate())}.${pad(we.getMonth()+1)}.${we.getFullYear()}`;
    $('sched').innerHTML = '<div class="empty">Загрузка…</div>';

    let entries = [];
    try {
        const r = await Auth.apiFetch('/api/portal/week?week_start=' + isoDate(ws));
        entries = r.ok ? await r.json() : [];
    } catch(e){ entries = []; }
    if (!Array.isArray(entries)) entries = [];

    if (!entries.length){
        $('sched').innerHTML = '<div class="empty">На этой неделе занятий нет.</div>';
        return;
    }

    const byDay = {};
    entries.forEach(e => { const d=(e.date||'').slice(0,10); (byDay[d]=byDay[d]||[]).push(e); });

    let html = '';
    for (let i = 0; i < 7; i++){
        const d = new Date(schedMonday); d.setDate(d.getDate()+i);
        const key = isoDate(d);
        const items = (byDay[key] || []).sort((a,b) => a.quant - b.quant);
        if (!items.length) continue;
        html += `<div class="day-group">
            <div class="day-head">${DOW_FULL[i]}, ${pad(d.getDate())}.${pad(d.getMonth()+1)}</div>
            ${items.map(schedRow).join('')}
        </div>`;
    }
    $('sched').innerHTML = html || '<div class="empty">На этой неделе занятий нет.</div>';
}

function schedRow(e){
    const time = quantTime(e.quant);
    if (e.entity_type === 'event' && e.event){
        const ev = e.event;
        return `<div class="srow"><div class="s-main">
            <div class="s-title"><span class="kind event">Концерт</span>${esc(ev.title || 'Концерт')}</div>
            ${ev.description ? `<div class="s-meta">${esc(ev.description)}</div>` : ''}
        </div><div class="s-time">${time}</div></div>`;
    }
    if (e.entity_type === 'exam' && e.exam){
        const ex = e.exam;
        const meta = [ex.commission_name, ex.room_name].filter(Boolean).join(' · ');
        return `<div class="srow"><div class="s-main">
            <div class="s-title"><span class="kind exam">Экзамен</span>${esc(ex.discipline_name || ex.exam_type || 'Экзамен')}</div>
            ${meta ? `<div class="s-meta">${esc(meta)}</div>` : ''}
        </div><div class="s-time">${time}</div></div>`;
    }
    const s = e.session || {};
    const l = s.lesson || {};
    const disc = l.discipline ? l.discipline.name : 'Занятие';
    const meta = [teacherName(l.teacher), s.room ? s.room.name : null].filter(Boolean).join(' · ');
    const cancelled = s.status === 'cancelled';
    return `<div class="srow"><div class="s-main">
        <div class="s-title"><span class="kind session">Занятие</span>${esc(disc)}${cancelled ? '<span class="tag-cancel">отменено</span>' : ''}</div>
        ${meta ? `<div class="s-meta">${esc(meta)}</div>` : ''}
    </div><div class="s-time">${time}</div></div>`;
}

// домашние задания
async function loadHomeworks(){
    let hw = [];
    try { hw = await (await Auth.apiFetch('/api/portal/homeworks')).json(); }
    catch(e){ hw = []; }
    if (!Array.isArray(hw)) hw = [];

    hw.sort((a,b) => (a.is_completed - b.is_completed) || String(b.created_at||'').localeCompare(String(a.created_at||'')));
    const top = hw.slice(0, 8);

    if (!top.length){
        $('hw').innerHTML = '<div class="empty">Домашних заданий нет.</div>';
        return;
    }
    $('hw').innerHTML = top.map(h => `
        <div class="row">
            <div class="t">${esc(h.description || '—')}</div>
            <div class="m">${fmtRu(h.created_at)}${h.comment ? ' · отзыв: ' + esc(h.comment) : ''}</div>
            <span class="badge ${h.is_completed ? 'done' : 'open'}">${h.is_completed ? 'Выполнено' : 'В работе'}</span>
        </div>`).join('');
}

init();