Auth.requireRole(['teacher', 'admin']);

let me = null;
let teacherId = null;       // null => админ видит все ДЗ
let isAdmin = false;
let students = [];
let allHw = [];
let filter = 'all';                 // all | open | done
const expanded = new Set();         // id раскрытых строк
const confirming = new Set();       // id строк в режиме «подтвердите удаление»

const $ = id => document.getElementById(id);
function esc(s){ const d = document.createElement('div'); d.textContent = s == null ? '' : s; return d.innerHTML; }
function studentName(l){ return l ? (l.student_full_name || l.contact_full_name || ('Лид #' + l.id)) : ''; }

function fmtDate(iso){
    if (!iso) return '—';
    const d = new Date(iso);
    if (isNaN(d)) return '—';
    return `${String(d.getDate()).padStart(2,'0')}.${String(d.getMonth()+1).padStart(2,'0')}.${d.getFullYear()}`;
}

// инициализация
async function init(){
    const r = await Auth.apiFetch('/api/auth/me');
    if (r.status === 401){ window.location.href = '/login'; return; }
    me = await r.json();
    isAdmin = me.role && me.role.code === 'admin';
    teacherId = isAdmin ? null : me.id;
    $('who').textContent = isAdmin
        ? 'Все задания сети'
        : `${me.full_name} · выданные и выполненные`;

    await loadStudents();
    await loadHomeworks();

    // фильтры
    $('filters').addEventListener('click', (e) => {
        const pill = e.target.closest('.pill');
        if (!pill) return;
        filter = pill.dataset.f;
        document.querySelectorAll('.pill').forEach(p => p.classList.toggle('active', p === pill));
        render();
    });

    // модалка
    $('open-create').addEventListener('click', openModal);
    $('create-cancel').addEventListener('click', closeModal);
    $('create-save').addEventListener('click', onCreate);
    $('create-overlay').addEventListener('click', (e) => { if (e.target.id === 'create-overlay') closeModal(); });

    // делегирование кликов по таблице
    $('hw-tbody').addEventListener('click', onTableClick);
}

async function loadStudents(){
    try { students = await (await Auth.apiFetch('/api/leads?is_student=true')).json(); }
    catch(e){ students = []; }
    if (!Array.isArray(students)) students = [];

    const sel = $('hw-student');
    sel.innerHTML = students.length
        ? '<option value="">— выберите ученика —</option>' + students.map(l =>
            `<option value="${l.id}">${esc(studentName(l))}${l.discipline ? ' · ' + esc(l.discipline.name) : ''}</option>`).join('')
        : '<option value="">Учеников нет — сначала зачислите через «Конверсию»</option>';
}

async function loadHomeworks(){
    $('loading').classList.remove('hidden');
    try {
        const url = teacherId ? '/api/homeworks?teacher_id=' + teacherId : '/api/homeworks';
        allHw = await (await Auth.apiFetch(url)).json();
    } catch(e){ allHw = []; }
    if (!Array.isArray(allHw)) allHw = [];
    $('loading').classList.add('hidden');
    render();
}

// фильтрация + счётчики
function counts(){
    return {
        all: allHw.length,
        open: allHw.filter(h => !h.is_completed).length,
        done: allHw.filter(h => h.is_completed).length,
    };
}
function filteredHw(){
    if (filter === 'open') return allHw.filter(h => !h.is_completed);
    if (filter === 'done') return allHw.filter(h => h.is_completed);
    return allHw;
}

// отрисовка 
function statusBadge(h){
    return h.is_completed
        ? '<span class="badge done">Выполнено</span>'
        : '<span class="badge open">В работе</span>';
}

function detailHtml(h){
    const toggle = h.is_completed
        ? `<button class="btn-sm btn-undo" data-act="toggle" data-id="${h.id}" data-done="1">Вернуть в работу</button>`
        : `<button class="btn-sm btn-ok"   data-act="toggle" data-id="${h.id}" data-done="0">Отметить выполненным</button>`;

    const del = confirming.has(h.id)
        ? `<span style="display:inline-flex; gap:6px; margin-left:auto;">
               <button class="btn-sm btn-confirm" data-act="del-yes" data-id="${h.id}">Удалить</button>
               <button class="btn-sm btn-cancel" data-act="del-no" data-id="${h.id}">Отмена</button>
           </span>`
        : `<button class="btn-sm btn-del" data-act="del-ask" data-id="${h.id}">Удалить</button>`;

    return `<tr class="detail-row" data-detail="${h.id}"><td colspan="4">
        <div class="detail-box">
            <div class="lbl">Полный текст задания</div>
            <div class="full-task">${esc(h.description) || '—'}</div>

            <div class="lbl">Отзыв преподавателя</div>
            <textarea class="hw-comment" data-id="${h.id}" placeholder="Комментарий по выполнению...">${esc(h.comment || '')}</textarea>

            <div class="detail-actions">
                ${toggle}
                <button class="btn-sm btn-save" data-act="save" data-id="${h.id}">Сохранить отзыв</button>
                ${del}
            </div>
            <div class="row-msg hidden" data-msg="${h.id}"></div>
        </div>
    </td></tr>`;
}

function rowHtml(h){
    const stud = students.find(s => s.id === h.student_id);
    const disc = stud && stud.discipline ? stud.discipline.name : '';
    const name = h.student_name || studentName(stud);
    const open = expanded.has(h.id);

    const main = `<tr class="hw-row ${open ? 'open' : ''}" data-row="${h.id}">
        <td class="col-student">${esc(name)}</td>
        <td class="col-date">${fmtDate(h.created_at)}</td>
        <td class="col-task">
            ${esc(h.description) || '<span style="color:#c0392b;">— нет текста —</span>'}
            ${disc ? `<div class="disc">${esc(disc)}</div>` : ''}
        </td>
        <td class="col-status">${statusBadge(h)}<span class="chev">▶</span></td>
    </tr>`;

    return main + (open ? detailHtml(h) : '');
}

function render(){
    const c = counts();
    $('cnt-all').textContent = c.all;
    $('cnt-open').textContent = c.open;
    $('cnt-done').textContent = c.done;

    const list = filteredHw();
    $('empty').classList.toggle('hidden', list.length > 0);
    $('hw-tbody').innerHTML = list.map(rowHtml).join('');
}

// ── клики по таблице ──
function rowMsg(id, text, ok){
    const el = document.querySelector(`[data-msg="${id}"]`);
    if (!el) return;
    el.textContent = text;
    el.className = 'row-msg ' + (ok ? 'ok' : 'err');
    el.classList.remove('hidden');
}

async function onTableClick(e){
    const actBtn = e.target.closest('button[data-act]');
    if (actBtn){
        e.stopPropagation();
        const id = parseInt(actBtn.dataset.id, 10);
        const act = actBtn.dataset.act;

        if (act === 'del-ask'){ confirming.add(id); render(); return; }
        if (act === 'del-no'){ confirming.delete(id); render(); return; }

        if (act === 'del-yes'){
            try {
                const r = await Auth.apiFetch('/api/homeworks/' + id, { method:'DELETE' });
                if (r.ok){ allHw = allHw.filter(h => h.id !== id); confirming.delete(id); expanded.delete(id); render(); }
                else rowMsg(id, 'Не удалось удалить', false);
            } catch(err){ rowMsg(id, 'Сетевая ошибка', false); }
            return;
        }

        if (act === 'toggle'){
            const done = actBtn.dataset.done === '1';      // текущее состояние
            try {
                const r = await Auth.apiFetch('/api/homeworks/' + id, {
                    method:'PATCH', headers:{ 'Content-Type':'application/json' },
                    body: JSON.stringify({ is_completed: !done }),
                });
                const data = await r.json();
                if (r.ok){ const i = allHw.findIndex(h => h.id === id); if (i >= 0) allHw[i] = data; render(); }
                else rowMsg(id, 'Ошибка сохранения', false);
            } catch(err){ rowMsg(id, 'Сетевая ошибка', false); }
            return;
        }

        if (act === 'save'){
            const ta = document.querySelector(`textarea.hw-comment[data-id="${id}"]`);
            const comment = ta ? ta.value.trim() : '';
            try {
                const r = await Auth.apiFetch('/api/homeworks/' + id, {
                    method:'PATCH', headers:{ 'Content-Type':'application/json' },
                    body: JSON.stringify({ comment: comment || null }),
                });
                const data = await r.json();
                if (r.ok){ const i = allHw.findIndex(h => h.id === id); if (i >= 0) allHw[i] = data; rowMsg(id, 'Отзыв сохранён', true); }
                else rowMsg(id, 'Ошибка сохранения', false);
            } catch(err){ rowMsg(id, 'Сетевая ошибка', false); }
            return;
        }
        return;
    }

    // клик по строке — раскрыть/свернуть
    const row = e.target.closest('.hw-row');
    if (!row) return;
    const id = parseInt(row.dataset.row, 10);
    if (expanded.has(id)) expanded.delete(id); else expanded.add(id);
    confirming.delete(id);
    render();
}

// ── модалка создания ──
function openModal(){
    $('create-msg').classList.add('hidden');
    $('hw-desc').value = '';
    $('hw-student').value = '';
    $('create-overlay').classList.add('show');
}
function closeModal(){ $('create-overlay').classList.remove('show'); }

function createMsg(text, type){
    const el = $('create-msg');
    el.textContent = text; el.className = `message ${type}`; el.classList.remove('hidden');
}

async function onCreate(){
    $('create-msg').classList.add('hidden');
    const studentId = parseInt($('hw-student').value, 10);
    if (!studentId){ createMsg('Выберите ученика', 'error'); return; }
    const description = $('hw-desc').value.trim();
    if (!description){ createMsg('Введите текст задания', 'error'); return; }

    // teacher_id: преподаватель выдаёт от себя; админ — тоже от своего id (бэкенд требует роль teacher для POST,
    // поэтому у админа создание может быть недоступно — об этом будет понятная ошибка)
    const tId = teacherId || me.id;
    try {
        const r = await Auth.apiFetch('/api/homeworks', {
            method:'POST', headers:{ 'Content-Type':'application/json' },
            body: JSON.stringify({ teacher_id: tId, student_id: studentId, description }),
        });
        const data = await r.json();
        if (r.ok){
            closeModal();
            await loadHomeworks();
        } else {
            const t = Array.isArray(data.detail) ? data.detail.map(x => x.msg).join('; ') : (data.detail || 'Ошибка');
            createMsg('Ошибка: ' + t, 'error');
        }
    } catch(err){ createMsg('Сетевая ошибка: ' + err.message, 'error'); }
}

init();
