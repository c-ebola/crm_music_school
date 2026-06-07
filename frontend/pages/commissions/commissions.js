Auth.requireRole(['methodist', 'branch_admin', 'admin']);

const ROLE = { chairman: 'Председатель', member: 'Член комиссии' };

let staff = [];
let commissions = [];
let pending = [];
const confirming = new Set();
const errById = {};

const $ = id => document.getElementById(id);
function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function staffName(id){ const u = staff.find(s => s.id === id); return u ? (u.full_name || u.email) : ('#'+id); }

function staffOptions(){
    return '<option value="">— выберите —</option>' + staff.map(u =>
        `<option value="${u.id}">${esc(u.full_name || u.email)} — ${esc(u.role ? u.role.name : '')}</option>`
    ).join('');
}

async function loadStaff(){
    try { const r = await Auth.apiFetch('/api/users/staff'); staff = await r.json(); }
    catch(e){ staff = []; }
    $('c-user').innerHTML = staffOptions();
}

async function loadCommissions(){
    $('loading').classList.remove('hidden');
    try { const r = await Auth.apiFetch('/api/commissions'); commissions = await r.json(); }
    catch(e){ commissions = []; }
    $('loading').classList.add('hidden');
    render();
}

function renderPending(){
    $('c-pending').innerHTML = pending.map((m, i) =>
        `<span class="chip ${m.role}">${esc(staffName(m.user_id))}
            <span style="opacity:.7">· ${ROLE[m.role]}</span>
            <span class="x" data-rm="${i}">×</span></span>`
    ).join('');
}
$('c-add').addEventListener('click', () => {
    const uid = parseInt($('c-user').value, 10);
    if (!uid) return;
    if (pending.some(m => m.user_id === uid)) return;
    pending.push({ user_id: uid, role: $('c-role').value });
    $('c-user').value = '';
    renderPending();
});
$('c-pending').addEventListener('click', (e) => {
    const x = e.target.closest('[data-rm]');
    if (!x) return;
    pending.splice(parseInt(x.dataset.rm, 10), 1);
    renderPending();
});

function createMsg(text, type){
    const el = $('create-msg'); el.innerHTML = text; el.className = `message ${type}`; el.classList.remove('hidden');
}

$('commission-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    $('create-msg').classList.add('hidden');
    const name = $('c-name').value.trim();
    if (!name){ createMsg('Введите название', 'error'); return; }
    try {
        const r = await Auth.apiFetch('/api/commissions', {
            method:'POST', headers:{ 'Content-Type':'application/json' },
            body: JSON.stringify({ name, members: pending }),
        });
        const data = await r.json();
        if (r.ok){
            createMsg(`Комиссия «${esc(data.name)}» создана`, 'success');
            $('commission-form').reset(); pending = []; renderPending();
            await loadCommissions();
        } else { createMsg('Ошибка: ' + esc(data.detail || 'не удалось создать'), 'error'); }
    } catch(err){ createMsg('Сетевая ошибка: ' + esc(err.message), 'error'); }
});

function memberChips(c){
    if (!c.members.length) return '<span style="color:#a1a1a6;font-size:12px;">нет участников</span>';
    return c.members.map(m =>
        `<span class="chip ${m.role}">${esc(m.user_name || ('#'+m.user_id))}
            <span class="badge role-${m.role}">${ROLE[m.role]}</span>
            <span class="x" data-act="rmmember" data-cid="${c.id}" data-mid="${m.id}">×</span></span>`
    ).join('');
}

function cardHtml(c){
    const err = errById[c.id] ? `<div class="cm-err">${esc(errById[c.id])}</div>` : '';
    const actions = confirming.has(c.id)
        ? `<div class="confirm-row">
               <button class="btn-confirm" data-act="confirm" data-id="${c.id}">Удалить</button>
               <button class="btn-cancel" data-act="cancel" data-id="${c.id}">Отмена</button>
           </div>`
        : `<button class="btn-del" data-act="ask" data-id="${c.id}">Удалить</button>`;
    return `<div class="cm-card">
        <div class="cm-name">${esc(c.name)}</div>
        <div class="chips">${memberChips(c)}</div>
        <div class="mini-add">
            <select data-userpick="${c.id}">${staffOptions()}</select>
            <select data-rolepick="${c.id}">
                <option value="member">Член</option>
                <option value="chairman">Председатель</option>
            </select>
            <button class="btn-add" data-act="addmember" data-cid="${c.id}">+</button>
        </div>
        ${err}
        <div class="cm-foot"><span class="cm-id">ID ${c.id}</span>${actions}</div>
    </div>`;
}

function render(){
    $('count').textContent = `(${commissions.length})`;
    $('empty').classList.toggle('hidden', commissions.length > 0);
    $('cards').innerHTML = commissions.map(cardHtml).join('');
}

$('cards').addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-act]');
    if (!btn) return;
    const act = btn.dataset.act;
    if (act === 'ask'){ confirming.add(+btn.dataset.id); delete errById[+btn.dataset.id]; render(); return; }
    if (act === 'cancel'){ confirming.delete(+btn.dataset.id); render(); return; }
    if (act === 'confirm'){
        const id = +btn.dataset.id;
        try {
            const r = await Auth.apiFetch('/api/commissions/' + id, { method:'DELETE' });
            if (r.ok){ commissions = commissions.filter(c => c.id !== id); confirming.delete(id); delete errById[id]; }
            else { const d = await r.json().catch(()=>({})); errById[id] = d.detail || `Ошибка (HTTP ${r.status})`; confirming.delete(id); }
        } catch(err){ errById[id] = 'Сетевая ошибка: ' + err.message; confirming.delete(id); }
        render(); return;
    }
    if (act === 'addmember'){
        const cid = +btn.dataset.cid;
        const uid = parseInt(document.querySelector(`[data-userpick="${cid}"]`).value, 10);
        const role = document.querySelector(`[data-rolepick="${cid}"]`).value;
        if (!uid) return;
        try {
            const r = await Auth.apiFetch(`/api/commissions/${cid}/members`, {
                method:'POST', headers:{ 'Content-Type':'application/json' },
                body: JSON.stringify({ user_id: uid, role }),
            });
            const data = await r.json();
            if (r.ok){ delete errById[cid]; await loadCommissions(); return; }
            else { const data = await r.json().catch(()=>({})); errById[cid] = data.detail || 'Не удалось добавить'; }
        } catch(err){ errById[cid] = 'Сетевая ошибка: ' + err.message; }
        render(); return;
    }
    if (act === 'rmmember'){
        const cid = +btn.dataset.cid, mid = +btn.dataset.mid;
        try {
            const r = await Auth.apiFetch(`/api/commissions/${cid}/members/${mid}`, { method:'DELETE' });
            const data = await r.json();
            if (r.ok){ delete errById[cid]; await loadCommissions(); return; }
            else { const data = await r.json().catch(()=>({})); errById[cid] = data.detail || 'Не удалось убрать'; }
        } catch(err){ errById[cid] = 'Сетевая ошибка: ' + err.message; }
        render(); return;
    }
});

(async () => { await loadStaff(); await loadCommissions(); })();
