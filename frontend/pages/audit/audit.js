Auth.requireRole(['branch_admin', 'admin']);

const PAGE = 100;
let offset = 0;
let loadedAll = [];
let exhausted = false;
let activeCat = 'all';

// порядок и оформление категорий
const CAT = {
    auth:    { label: 'Авторизации',   bg:'#eef3ff', color:'#274690', dot:'#3b6fd4' },
    delete:  { label: 'Удаления',      bg:'#fde7e7', color:'#8c1f1f', dot:'#d04545' },
    price:   { label: 'Изменение цен', bg:'#fff3e0', color:'#9a6400', dot:'#e0a23a' },
    payment: { label: 'Оплаты',        bg:'#e7f6ea', color:'#1f7a3d', dot:'#2faa55' },
    create:  { label: 'Создание',      bg:'#eef7ef', color:'#1f7a3d', dot:'#5ac46f' },
    update:  { label: 'Изменения',     bg:'#eef3ff', color:'#274690', dot:'#3b6fd4' },
    other:   { label: 'Прочее',        bg:'#f0f0f3', color:'#555',    dot:'#aaa'    },
};
const CAT_ORDER = ['auth','delete','price','payment','create','update','other'];

const $ = id => document.getElementById(id);
function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function pad(n){ return String(n).padStart(2,'0'); }

function categorize(r){
    const path = r.path || '';
    const parts = path.split('/').filter(Boolean);   // ['api','subscription-plans','3']
    const seg = parts[1] || '';
    if (path.startsWith('/api/auth')) return 'auth';
    if (r.method === 'DELETE') return 'delete';
    if (seg === 'subscription-plans' && (r.method === 'PATCH' || r.method === 'PUT')) return 'price';
    if (seg === 'payments' && r.method === 'POST') return 'payment';
    if (r.method === 'POST') return 'create';
    if (r.method === 'PATCH' || r.method === 'PUT') return 'update';
    return 'other';
}

function fmtWhen(iso){
    if (!iso) return '';
    const d = new Date(iso);
    const now = new Date();
    const day0 = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const that0 = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const diff = Math.round((day0 - that0) / 86400000);
    const hm = `${pad(d.getHours())}:${pad(d.getMinutes())}`;
    if (diff === 0) return `Сегодня ${hm}`;
    if (diff === 1) return `Вчера ${hm}`;
    return `${pad(d.getDate())}.${pad(d.getMonth()+1)}.${d.getFullYear()} ${hm}`;
}

function buildQuery(reset){
    const p = new URLSearchParams();
    p.set('limit', PAGE);
    p.set('offset', reset ? 0 : offset);
    if ($('f-from').value) p.set('date_from', $('f-from').value);
    if ($('f-to').value) p.set('date_to', $('f-to').value);
    return p.toString();
}

async function load(reset){
    if (reset){ offset = 0; loadedAll = []; exhausted = false; }
    $('loading').classList.remove('hidden');
    $('more').classList.add('hidden');
    let batch = [];
    try {
        const r = await Auth.apiFetch('/api/audit?' + buildQuery(reset));
        batch = r.ok ? await r.json() : [];
    } catch(e){ batch = []; }
    if (!Array.isArray(batch)) batch = [];
    $('loading').classList.add('hidden');

    batch.forEach(r => { r._cat = categorize(r); });
    loadedAll = loadedAll.concat(batch);
    offset += batch.length;
    if (batch.length < PAGE) exhausted = true;
    render();
}

function render(){
    // счётчики по категориям
    const counts = {};
    loadedAll.forEach(r => { counts[r._cat] = (counts[r._cat] || 0) + 1; });

    let pills = `<button class="pill ${activeCat==='all'?'active':''}" data-cat="all">Все типы <span class="c">${loadedAll.length}</span></button>`;
    CAT_ORDER.forEach(cat => {
        if (!counts[cat]) return;
        pills += `<button class="pill ${activeCat===cat?'active':''}" data-cat="${cat}">${esc(CAT[cat].label)} <span class="c">${counts[cat]}</span></button>`;
    });
    $('pills').innerHTML = pills;
    $('pills').querySelectorAll('.pill').forEach(p =>
        p.addEventListener('click', () => { activeCat = p.dataset.cat; render(); }));

    // строки
    const q = $('f-search').value.trim().toLowerCase();
    let list = loadedAll;
    if (activeCat !== 'all') list = list.filter(r => r._cat === activeCat);
    if (q) list = list.filter(r => (r.actor_name || '').toLowerCase().includes(q));

    $('feed-sub').textContent = `Показано ${list.length} ${q || activeCat!=='all' ? 'из ' + loadedAll.length + ' ' : ''}записей`;
    $('empty').classList.toggle('hidden', list.length > 0);
    $('rows').innerHTML = list.map(rowHtml).join('');
    $('more').classList.toggle('hidden', exhausted || activeCat !== 'all' || !!q);
}

function rowHtml(r){
    const c = CAT[r._cat] || CAT.other;
    const dot = r.status_code >= 400 ? '#d04545' : c.dot;
    const actor = [r.actor_name || 'Система', [r.actor_role, r.actor_branch].filter(Boolean).join(' · ')]
        .filter(Boolean);
    return `<div class="op">
        <span class="dot" style="background:${dot};"></span>
        <div>
            <div class="op-time">${esc(fmtWhen(r.created_at))}</div>
            <div class="op-badge" style="background:${c.bg};color:${c.color};">${esc(c.label)}</div>
        </div>
        <div>
            <div class="op-desc">${esc(actor[0])}${actor[1] ? ' — ' + esc(r.action || '') : esc(' ' + (r.action || ''))}</div>
            <div class="op-sub">${actor[1] ? esc(actor[1]) + ' · ' : ''}<span class="path">${esc(r.method)} ${esc(r.path)}</span> · код ${r.status_code}</div>
        </div>
    </div>`;
}

async function init(){
    try {
        const me = await (await Auth.apiFetch('/api/auth/me')).json();
        const isAdmin = (me.role && me.role.code === 'admin') || me.is_superuser;
        $('who').textContent = isAdmin
            ? 'Все важные операции сети с фиксацией пользователя и времени'
            : 'Операции вашего филиала с фиксацией пользователя и времени';
    } catch(e){}

    $('toggle-filters').addEventListener('click', () => $('filters').classList.toggle('show'));
    $('f-from').addEventListener('change', () => load(true));
    $('f-to').addEventListener('change', () => load(true));
    $('f-search').addEventListener('input', render);
    $('f-reset').addEventListener('click', () => {
        $('f-from').value=''; $('f-to').value=''; $('f-search').value=''; activeCat='all'; load(true);
    });
    $('more').addEventListener('click', () => load(false));

    await load(true);
}

init();