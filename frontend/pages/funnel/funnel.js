const $ = id => document.getElementById(id);
function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':String(s); return d.innerHTML; }

const STAGES = [
  { key:'new',             title:'Новый лид' },
  { key:'in_progress',     title:'Связались' },
  { key:'trial_scheduled', title:'Пробный урок' },
  { key:'contract',        title:'Договор' },
  { key:'converted',       title:'Оплачено', terminal:true },
  { key:'rejected',        title:'Отказ',    rejected:true },
];
const CH = { website:'сайт', phone:'звонок', social:'соцсети', referral:'сарафан', advertising:'реклама', other:'другое' };

let leads = [];
let dragId = null;

async function boot(){
  if (!(await Auth.requireRole(['manager','branch_admin','admin']))) return;
  await loadDisciplines();
  await loadLeads();
}

async function loadDisciplines(){
  let list = [];
  try { const r = await Auth.apiFetch('/api/disciplines?only_active=true'); list = await r.json(); } catch(e){}
  $('f-discipline').innerHTML = '<option value="">Все дисциплины</option>' +
    (Array.isArray(list)?list:[]).map(d=>`<option value="${d.id}">${esc(d.name)}</option>`).join('');
}

async function loadLeads(){
  try { const r = await Auth.apiFetch('/api/leads'); const d = await r.json(); leads = Array.isArray(d)?d:[]; }
  catch(e){ leads = []; }
  render();
}

function filtered(){
  const ch = $('f-channel').value, disc = $('f-discipline').value;
  return leads.filter(l =>
    (!ch || l.channel === ch) &&
    (!disc || String(l.discipline_id) === disc)
  );
}

function cardHtml(l){
  const name = l.student_full_name || l.contact_full_name || ('Лид №'+l.id);
  const bits = [];
  if (l.discipline) bits.push(esc(l.discipline.name));
  if (l.channel) bits.push(esc(CH[l.channel] || l.channel));
  const sub = l.manager_comment ? esc(l.manager_comment) : bits.join(' · ');
  const drag = (l.status === 'converted') ? 'false' : 'true';
  return `<div class="fcard" draggable="${drag}" data-id="${l.id}">
    <div class="fc-name">${esc(name)}</div>
    <div class="fc-sub">${sub}</div>
  </div>`;
}

function render(){
  const data = filtered();
  const byStage = {};
  STAGES.forEach(s => byStage[s.key] = []);
  data.forEach(l => { if (byStage[l.status]) byStage[l.status].push(l); });

  $('board').innerHTML = STAGES.map((s, i) => {
    const cards = byStage[s.key];
    let pct;
    if (s.rejected)      pct = cards.length ? `✗ ${cards.length}` : '✗ 0';
    else if (s.terminal) pct = '✓ готово';
    else {
      const next = byStage[STAGES[i+1].key].length;
      pct = '→ ';
    }
    const body = cards.length ? cards.map(cardHtml).join('') : '<div class="funnel-empty">пусто</div>';
    return `<div class="fcol" data-stage="${s.key}">
      <div class="fcol-head stage-${s.key}">
        <div class="fh-title">${esc(s.title)}</div>
        <div class="fh-pct">${pct}</div>
      </div>
      <div class="fcol-sub"><span>${esc(s.title)}</span><span class="fcount">${cards.length}</span></div>
      <div class="fcol-body" data-stage="${s.key}">${body}</div>
    </div>`;
  }).join('');
  wireDnd();
}

function wireDnd(){
  document.querySelectorAll('.fcard[draggable="true"]').forEach(c => {
    c.addEventListener('dragstart', () => { dragId = c.dataset.id; c.classList.add('dragging'); });
    c.addEventListener('dragend',   () => c.classList.remove('dragging'));
  });
  document.querySelectorAll('.fcol-body').forEach(b => {
    b.addEventListener('dragover',  e => { e.preventDefault(); b.classList.add('over'); });
    b.addEventListener('dragleave', () => b.classList.remove('over'));
    b.addEventListener('drop',      e => { e.preventDefault(); b.classList.remove('over'); onDrop(b.dataset.stage); });
  });
}

async function onDrop(stage){
  const id = dragId; dragId = null;
  if (!id) return;
  const lead = leads.find(l => String(l.id) === id);
  if (!lead || lead.status === stage) return;

  if (stage === 'converted'){
    window.location.href = '/convert';
    return;
  }

  const prev = lead.status;
  lead.status = stage;
  render();
  try {
    const r = await Auth.apiFetch('/api/leads/' + id + '/status', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: stage }),
    });
    if (!r.ok){
      const e = await r.json().catch(()=>({}));
      lead.status = prev; render();
      alert('Не удалось перенести: ' + (e.detail || ('HTTP ' + r.status)));
    } else {
      Object.assign(lead, await r.json());
      render();
    }
  } catch(e){
    lead.status = prev; render();
    alert('Сетевая ошибка: ' + e.message);
  }
}

['f-channel','f-discipline'].forEach(id => $(id).addEventListener('change', render));
$('btn-new').addEventListener('click', () => window.location.href = '/leads');

boot();
