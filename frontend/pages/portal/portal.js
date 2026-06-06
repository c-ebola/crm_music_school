const $ = id => document.getElementById(id);
function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':String(s); return d.innerHTML; }
function pad(n){ return String(n).padStart(2,'0'); }
function quantTime(q){ const s=9*60+(q-1)*60, e=s+45; return `${pad(Math.floor(s/60))}:${pad(s%60)}–${pad(Math.floor(e/60))}:${pad(e%60)}`; }

const DOW = ['Вс','Пн','Вт','Ср','Чт','Пт','Сб'];
function fmtDate(iso){
  const [y,m,d] = iso.slice(0,10).split('-').map(Number);
  const dt = new Date(y, m-1, d);
  return DOW[dt.getDay()] + ', ' + pad(d) + '.' + pad(m);
}
const SESS = { scheduled:'Запланировано', completed:'Проведено', cancelled:'Отменено' };

async function boot(){
  if (!(await Auth.requireRole(['student']))) return;
  let me;
  try {
    const r = await Auth.apiFetch('/api/portal/me');
    if (!r.ok){ document.querySelector('.content').innerHTML = '<div class="empty">Раздел доступен только ученикам.</div>'; return; }
    me = await r.json();
  } catch(e){ return; }
  $('hello').textContent = me.name || 'Мой кабинет';
  $('subtitle').textContent = me.discipline ? ('Дисциплина: ' + me.discipline) : '';
  loadSchedule();
  loadHomeworks();
}

async function loadSchedule(){
  let rows = [];
  try { rows = await (await Auth.apiFetch('/api/portal/schedule')).json(); } catch(e){}
  if (!Array.isArray(rows)) rows = [];
  const box = $('schedule');
  if (!rows.length){ box.innerHTML = '<div class="empty">Ближайших занятий нет.</div>'; return; }
  box.innerHTML = rows.map(r => `
    <div class="row-item">
      <div class="ri-when"><div class="ri-date">${esc(fmtDate(r.date))}</div><div class="ri-time">${esc(quantTime(r.quant))}</div></div>
      <div class="ri-main">
        <div class="ri-title">${esc(r.discipline || 'Занятие')}</div>
        <div class="ri-sub">${esc(r.teacher || '')}${r.room ? ' · ' + esc(r.room) : ''}</div>
      </div>
      <div class="ri-status st-${esc(r.status)}">${esc(SESS[r.status] || r.status)}</div>
    </div>`).join('');
}

async function loadHomeworks(){
  let rows = [];
  try { rows = await (await Auth.apiFetch('/api/portal/homeworks')).json(); } catch(e){}
  if (!Array.isArray(rows)) rows = [];
  const box = $('homeworks');
  if (!rows.length){ box.innerHTML = '<div class="empty">Домашних заданий нет.</div>'; return; }
  box.innerHTML = rows.map(h => `
    <div class="hw-item ${h.is_completed ? 'done' : ''}">
      <div class="hw-top">
        <span class="hw-status ${h.is_completed ? 's-done' : 's-open'}">${h.is_completed ? 'Выполнено' : 'К выполнению'}</span>
        <span class="hw-teacher">${esc(h.teacher_name || '')}</span>
      </div>
      <div class="hw-desc">${esc(h.description)}</div>
      ${h.comment ? `<div class="hw-comment">${esc(h.comment)}</div>` : ''}
    </div>`).join('');
}

boot();
