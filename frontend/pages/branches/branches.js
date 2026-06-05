Auth.requireRole(['admin']);

const KIND = { school: 'Учебный филиал', venue: 'Концертная площадка' };
const $ = id => document.getElementById(id);
function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }

let editing = null;
let cache = [];

function msg(text, type){ const el=$('form-msg'); el.textContent=text; el.className=`message ${type}`; el.classList.remove('hidden'); }
function clearMsg(){ $('form-msg').classList.add('hidden'); }

function resetForm(){
    editing = null;
    $('b-id').value=''; $('b-name').value=''; $('b-city').value=''; $('b-address').value='';
    $('b-kind').value='school'; $('b-active').checked=true;
    $('form-title').textContent='Новый филиал';
    $('save-btn').textContent='Создать';
    $('cancel-btn').classList.add('hidden');
    clearMsg();
}

async function load(){
    $('br-loading').classList.remove('hidden');
    try { cache = await (await Auth.apiFetch('/api/branches')).json(); } catch(e){ cache = []; }
    if (!Array.isArray(cache)) cache = [];
    $('br-loading').classList.add('hidden');
    $('br-count').textContent = `(${cache.length})`;
    $('br-empty').classList.toggle('hidden', cache.length>0);
    $('br-cards').innerHTML = cache.map(card).join('');
}

function card(b){
    const kindCls = b.kind === 'venue' ? 'venue' : 'school';
    const sub = [b.city, b.address].filter(Boolean).join(', ') || '—';
    return `<div class="br-card" data-id="${b.id}">
        <div style="display:flex; justify-content:space-between; gap:8px; align-items:start;">
            <div class="br-name">${esc(b.name)}</div>
            <span class="badge ${kindCls}">${esc(KIND[b.kind] || b.kind)}</span>
        </div>
        <div class="br-sub">${esc(sub)}</div>
        ${b.is_active ? '' : '<div style="margin-top:6px;"><span class="badge off">не активен</span></div>'}
        <div class="br-foot">
            <span class="br-id">ID ${b.id}</span>
            <span class="actions">
                <button class="btn-edit" data-act="edit" data-id="${b.id}">Изменить</button>
                <button class="btn-del" data-act="del" data-id="${b.id}">Удалить</button>
            </span>
        </div>
    </div>`;
}

$('branch-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    clearMsg();
    const name = $('b-name').value.trim();
    if (!name){ msg('Введите название', 'error'); return; }
    const payload = {
        name,
        kind: $('b-kind').value,
        city: $('b-city').value.trim() || null,
        address: $('b-address').value.trim() || null,
        is_active: $('b-active').checked,
    };
    try {
        const url = editing ? '/api/branches/' + editing : '/api/branches';
        const r = await Auth.apiFetch(url, {
            method: editing ? 'PATCH' : 'POST',
            headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload),
        });
        if (r.ok){ resetForm(); await load(); }
        else {
            const err = await r.json();
            const d = Array.isArray(err.detail) ? err.detail.map(x=>x.msg).join('; ') : (err.detail || r.status);
            msg('Ошибка: ' + d, 'error');
        }
    } catch(err){ msg('Сетевая ошибка: ' + err.message, 'error'); }
});

$('cancel-btn').addEventListener('click', resetForm);

$('br-cards').addEventListener('click', async (e) => {
    const btn = e.target.closest('button[data-act]'); if (!btn) return;
    const id = parseInt(btn.dataset.id, 10);
    if (btn.dataset.act === 'edit'){
        const item = cache.find(x => x.id === id);
        if (!item) return;
        editing = id;
        $('b-name').value = item.name || '';
        $('b-kind').value = item.kind || 'school';
        $('b-city').value = item.city || '';
        $('b-address').value = item.address || '';
        $('b-active').checked = !!item.is_active;
        $('form-title').textContent = 'Изменить филиал';
        $('save-btn').textContent = 'Сохранить';
        $('cancel-btn').classList.remove('hidden');
        clearMsg();
        window.scrollTo({ top: 0, behavior: 'smooth' });
        return;
    }
    if (btn.dataset.act === 'del'){
        if (!confirm('Удалить филиал? Связи у кабинетов/инструментов/лидов/сотрудников обнулятся.')) return;
        try {
            await Auth.apiFetch('/api/branches/' + id, { method:'DELETE' });
            if (editing === id) resetForm();
            await load();
        } catch(err){ alert('Ошибка: ' + err.message); }
    }
});

load();
