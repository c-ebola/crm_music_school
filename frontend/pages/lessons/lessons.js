Auth.requireRole(['methodist', 'branch_admin', 'admin']);

const FMT = { individual:'Индивидуальное', group:'Групповое', online:'Онлайн' };
const LVL = { beginner:'Начинающий', intermediate:'Средний', advanced:'Продвинутый' };

let allLessons = [];
const confirming = new Set();   // id уроков в режиме подтверждения удаления
const errById = {};             // id > текст ошибки удаления

const $ = id => document.getElementById(id);
function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function teacherName(t){ return t ? [t.last_name, t.first_name].filter(Boolean).join(' ') : ''; }

// справочники
async function loadRefs(){
    try {
        const [dr, tr] = await Promise.all([
            Auth.apiFetch('/api/disciplines?only_active=true'),
            Auth.apiFetch('/api/users/teachers'),
        ]);
        const discs = await dr.json();
        const teachers = await tr.json();

        const discOpts = discs.map(d => `<option value="${d.id}">${esc(d.name)}</option>`).join('');
        $('discipline_id').innerHTML = '<option value="">— выберите —</option>' + discOpts;
        $('f-discipline').innerHTML = '<option value="">Все дисциплины</option>' + discOpts;

        const tOpts = teachers.map(t => {
            const fio = teacherName(t) || t.email;
            return `<option value="${t.id}">${esc(fio)}</option>`;
        }).join('');
        $('teacher_id').innerHTML = '<option value="">— не назначен —</option>' + tOpts;
        $('f-teacher').innerHTML = '<option value="">Все преподаватели</option>' + tOpts;
    } catch(e){ /* справочники могут не загрузиться — форма всё равно работает */ }
}

//  список уроков 
async function loadLessons(){
    $('loading').classList.remove('hidden');
    try {
        const r = await Auth.apiFetch('/api/lessons');
        allLessons = await r.json();
    } catch(e){ allLessons = []; }
    $('loading').classList.add('hidden');
    render();
}

function filtered(){
    const q = $('f-search').value.trim().toLowerCase();
    const d = $('f-discipline').value;
    const t = $('f-teacher').value;
    return allLessons.filter(l => {
        if (d && String(l.discipline_id) !== d) return false;
        if (t && String(l.teacher_id) !== t) return false;
        if (q){
            const hay = `${l.discipline ? l.discipline.name : ''} ${teacherName(l.teacher)}`.toLowerCase();
            if (!hay.includes(q)) return false;
        }
        return true;
    });
}

function cardHtml(l){
    const disc = l.discipline ? l.discipline.name : '—';
    const fio = teacherName(l.teacher);
    const fmt = l.lesson_type
        ? `<span class="badge fmt-${l.lesson_type}">${esc(FMT[l.lesson_type]||l.lesson_type)}</span>` : '';
    const lvl = l.level ? `<span class="badge lvl">${esc(LVL[l.level]||l.level)}</span>` : '';
    const err = errById[l.id] ? `<div class="lc-err">${esc(errById[l.id])}</div>` : '';

    const actions = confirming.has(l.id)
        ? `<div class="confirm-row">
               <button class="btn-confirm" data-act="confirm" data-id="${l.id}">Удалить</button>
               <button class="btn-cancel" data-act="cancel" data-id="${l.id}">Отмена</button>
           </div>`
        : `<button class="btn-del" data-act="ask" data-id="${l.id}">Удалить</button>`;

    return `<div class="lesson-card" data-fmt="${esc(l.lesson_type||'')}">
        <div class="lc-top">
            <span class="lc-disc">${esc(disc)}</span>
            ${fmt}
        </div>
        <div class="lc-teacher ${fio ? '' : 'none'}">${fio ? esc(fio) : 'Преподаватель не назначен'}</div>
        <div class="lc-meta">${lvl}<span>до ${l.max_students} уч.</span></div>
        ${err}
        <div class="lc-foot">
            <span class="lc-id">ID ${l.id}</span>
            ${actions}
        </div>
    </div>`;
}

function render(){
    const list = filtered();
    $('count').textContent = `(${list.length})`;
    $('empty').classList.toggle('hidden', list.length > 0);
    $('cards').innerHTML = list.map(cardHtml).join('');
}

//удаление (делегирование)
$('cards').addEventListener('click', async (e) => {
    const btn = e.target.closest('button[data-act]');
    if (!btn) return;
    const id = parseInt(btn.dataset.id, 10);
    const act = btn.dataset.act;

    if (act === 'ask'){ confirming.add(id); delete errById[id]; render(); return; }
    if (act === 'cancel'){ confirming.delete(id); render(); return; }
    if (act === 'confirm'){
        try {
            const r = await Auth.apiFetch('/api/lessons/' + id, { method:'DELETE' });
            if (r.ok){
                allLessons = allLessons.filter(l => l.id !== id);
                confirming.delete(id); delete errById[id];
            } else {
                const data = await r.json().catch(() => ({}));
                errById[id] = data.detail || `Не удалось удалить (HTTP ${r.status})`;
                confirming.delete(id);
            }
        } catch(err){
            errById[id] = 'Сетевая ошибка: ' + err.message;
            confirming.delete(id);
        }
        render();
    }
});

//фильтры 
['f-search','f-discipline','f-teacher'].forEach(id => {
    $(id).addEventListener('input', render);
});
$('f-reset').addEventListener('click', () => {
    $('f-search').value = ''; $('f-discipline').value = ''; $('f-teacher').value = '';
    render();
});

// создание 
$('lesson_type').addEventListener('change', () => {
    const v = $('lesson_type').value;
    if (v === 'group') $('max_students').value = 8;
    else if (v === 'individual' || v === 'online') $('max_students').value = 1;
});

function createMsg(text, type){
    const el = $('create-msg');
    el.innerHTML = text; el.className = `message ${type}`; el.classList.remove('hidden');
}

$('lesson-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    $('create-msg').classList.add('hidden');
    if (!$('discipline_id').value){ createMsg('Выберите дисциплину', 'error'); return; }

    const payload = {
        discipline_id: parseInt($('discipline_id').value, 10),
        max_students: parseInt($('max_students').value, 10) || 1,
    };
    if ($('teacher_id').value)  payload.teacher_id = parseInt($('teacher_id').value, 10);
    if ($('lesson_type').value) payload.lesson_type = $('lesson_type').value;
    if ($('level').value)       payload.level = $('level').value;

    try {
        const r = await Auth.apiFetch('/api/lessons', {
            method:'POST',
            headers:{ 'Content-Type':'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await r.json();
        if (r.ok){
            createMsg(`Урок №${data.id} создан`, 'success');
            $('lesson-form').reset(); $('max_students').value = 1;
            await loadLessons();
        } else {
            const text = Array.isArray(data.detail)
                ? data.detail.map(x => `${x.loc.slice(-1)[0]}: ${x.msg}`).join('; ')
                : (data.detail || 'Неизвестная ошибка');
            createMsg('Ошибка: ' + esc(text), 'error');
        }
    } catch(err){ createMsg('Сетевая ошибка: ' + esc(err.message), 'error'); }
});

// init
loadRefs();
loadLessons();