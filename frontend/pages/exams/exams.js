Auth.requireRole(['methodist', 'branch_admin', 'admin']);

const LVL = { beginner:'Начинающий', intermediate:'Средний', advanced:'Продвинутый' };

let exams = [];
const confirming = new Set();
const errById = {};

const $ = id => document.getElementById(id);
function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }

async function loadRefs(){
    try {
        const [dr, cr] = await Promise.all([
            Auth.apiFetch('/api/disciplines?only_active=true'),
            Auth.apiFetch('/api/commissions'),
        ]);
        const discs = await dr.json();
        const comms = await cr.json();
        const discOpts = discs.map(d => `<option value="${d.id}">${esc(d.name)}</option>`).join('');
        $('e-discipline').innerHTML = '<option value="">— выберите —</option>' + discOpts;
        $('f-discipline').innerHTML = '<option value="">Все дисциплины</option>' + discOpts;
        $('e-commission').innerHTML = '<option value="">— не назначена —</option>' +
            comms.map(c => `<option value="${c.id}">${esc(c.name)}</option>`).join('');
    } catch(e){ /* справочники могут не загрузиться */ }
}

async function loadExams(){
    $('loading').classList.remove('hidden');
    try { const r = await Auth.apiFetch('/api/exams'); exams = await r.json(); }
    catch(e){ exams = []; }
    $('loading').classList.add('hidden');
    render();
}

function filtered(){
    const q = $('f-search').value.trim().toLowerCase();
    const d = $('f-discipline').value;
    return exams.filter(x => {
        if (d && String(x.discipline_id) !== d) return false;
        if (q){
            const hay = `${x.discipline_name||''} ${x.exam_type||''}`.toLowerCase();
            if (!hay.includes(q)) return false;
        }
        return true;
    });
}

function cardHtml(x){
    const type = x.exam_type ? `<span class="badge type">${esc(x.exam_type)}</span>` : '';
    const lvl = x.level ? `<span class="badge lvl">${esc(LVL[x.level]||x.level)}</span>` : '';
    const comm = x.commission_name
        ? `<div class="ex-comm">Комиссия: ${esc(x.commission_name)}</div>`
        : `<div class="ex-comm none">Комиссия не назначена</div>`;
    const err = errById[x.id] ? `<div class="ex-err">${esc(errById[x.id])}</div>` : '';
    const actions = confirming.has(x.id)
        ? `<div class="confirm-row">
               <button class="btn-confirm" data-act="confirm" data-id="${x.id}">Удалить</button>
               <button class="btn-cancel" data-act="cancel" data-id="${x.id}">Отмена</button>
           </div>`
        : `<button class="btn-del" data-act="ask" data-id="${x.id}">Удалить</button>`;
    return `<div class="ex-card">
        <div style="display:flex;justify-content:space-between;gap:8px;align-items:flex-start;">
            <span class="ex-disc">${esc(x.discipline_name || '—')}</span>${type}
        </div>
        <div class="ex-meta">${lvl}<span>до ${x.max_students} уч.</span></div>
        ${comm}
        ${err}
        <div class="ex-foot"><span class="ex-id">ID ${x.id}</span>${actions}</div>
    </div>`;
}

function render(){
    const list = filtered();
    $('count').textContent = `(${list.length})`;
    $('empty').classList.toggle('hidden', list.length > 0);
    $('cards').innerHTML = list.map(cardHtml).join('');
}

$('cards').addEventListener('click', async (e) => {
    const btn = e.target.closest('button[data-act]');
    if (!btn) return;
    const id = +btn.dataset.id, act = btn.dataset.act;
    if (act === 'ask'){ confirming.add(id); delete errById[id]; render(); return; }
    if (act === 'cancel'){ confirming.delete(id); render(); return; }
    if (act === 'confirm'){
        try {
            const r = await Auth.apiFetch('/api/exams/' + id, { method:'DELETE' });
            if (r.ok){ exams = exams.filter(x => x.id !== id); confirming.delete(id); delete errById[id]; }
            else { const d = await r.json().catch(()=>({})); errById[id] = d.detail || `Ошибка (HTTP ${r.status})`; confirming.delete(id); }
        } catch(err){ errById[id] = 'Сетевая ошибка: ' + err.message; confirming.delete(id); }
        render();
    }
});

['f-search','f-discipline'].forEach(id => $(id).addEventListener('input', render));
$('f-reset').addEventListener('click', () => { $('f-search').value=''; $('f-discipline').value=''; render(); });

function createMsg(text, type){
    const el = $('create-msg'); el.innerHTML = text; el.className = `message ${type}`; el.classList.remove('hidden');
}

$('exam-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    $('create-msg').classList.add('hidden');
    if (!$('e-discipline').value){ createMsg('Выберите дисциплину', 'error'); return; }
    const payload = {
        discipline_id: parseInt($('e-discipline').value, 10),
        max_students: parseInt($('e-max').value, 10) || 1,
    };
    if ($('e-type').value.trim()) payload.exam_type = $('e-type').value.trim();
    if ($('e-level').value) payload.level = $('e-level').value;
    if ($('e-commission').value) payload.commission_id = parseInt($('e-commission').value, 10);
    try {
        const r = await Auth.apiFetch('/api/exams', {
            method:'POST', headers:{ 'Content-Type':'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await r.json();
        if (r.ok){
            createMsg(`Экзамен №${data.id} создан`, 'success');
            $('exam-form').reset(); $('e-max').value = 1;
            await loadExams();
        } else {
            const text = Array.isArray(data.detail)
                ? data.detail.map(x => `${x.loc.slice(-1)[0]}: ${x.msg}`).join('; ')
                : (data.detail || 'Неизвестная ошибка');
            createMsg('Ошибка: ' + esc(text), 'error');
        }
    } catch(err){ createMsg('Сетевая ошибка: ' + esc(err.message), 'error'); }
});

loadRefs();
loadExams();
