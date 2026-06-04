Auth.requireRole(['teacher', 'admin']);

const token = localStorage.getItem('token');
if (!token) window.location.href = '/login';
const authHeaders = { 'Authorization': 'Bearer ' + token };

let me = null;
let teacherId = null;
let students = [];          // ученики (leads is_student=true)
let allHw = [];             // домашки текущего преподавателя
const confirming = new Set();

const $ = id => document.getElementById(id);
function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function studentName(l){ return l ? (l.student_full_name || l.contact_full_name || ('Лид #'+l.id)) : ''; }
function fmtDate(iso){
    if (!iso) return '';
    const d = new Date(iso);
    return `${String(d.getDate()).padStart(2,'0')}.${String(d.getMonth()+1).padStart(2,'0')}.${d.getFullYear()}`;
}

let createStudentId = null;
function setupTypeahead(inputEl, sugEl, onPick){
    inputEl.addEventListener('input', () => {
        const q = inputEl.value.trim().toLowerCase();
        if (!q){ sugEl.classList.add('hidden'); sugEl.innerHTML=''; return; }
        const matches = students.filter(l => studentName(l).toLowerCase().includes(q)).slice(0, 8);
        if (!matches.length){ sugEl.innerHTML = '<div class="sug-empty">Не найдено</div>'; sugEl.classList.remove('hidden'); return; }
        sugEl.innerHTML = matches.map(l => {
            const disc = l.discipline ? ' · ' + esc(l.discipline.name) : '';
            return `<div class="sug-item" data-id="${l.id}">${esc(studentName(l))}<span class="sug-sub">${disc}</span></div>`;
        }).join('');
        sugEl.classList.remove('hidden');
    });
    sugEl.addEventListener('click', (e) => {
        const it = e.target.closest('.sug-item'); if (!it) return;
        const id = parseInt(it.dataset.id, 10);
        inputEl.value = studentName(students.find(s => s.id === id));
        sugEl.classList.add('hidden');
        onPick(id);
    });
    document.addEventListener('click', (e) => {
        if (!sugEl.contains(e.target) && e.target !== inputEl) sugEl.classList.add('hidden');
    });
}

async function init(){
    const r = await Auth.apiFetch('/api/auth/me', { headers: authHeaders });
    if (r.status === 401){ localStorage.removeItem('token'); window.location.href='/login'; return; }
    me = await r.json();
    teacherId = me.id;
    $('who').textContent = `${me.full_name} (${me.role.name})`;

    await loadStudents();
    await loadHomeworks();

    setupTypeahead($('hw-student-input'), $('hw-student-sug'), (id) => {
        createStudentId = id; $('hw-student-clear').classList.remove('hidden');
    });
    $('hw-student-clear').addEventListener('click', () => {
        createStudentId = null; $('hw-student-input').value = ''; $('hw-student-clear').classList.add('hidden');
    });
    $('hw-form').addEventListener('submit', onCreate);
    ['f-search','f-status'].forEach(id => $(id).addEventListener('input', renderHomeworks));
}

async function loadStudents(){
    try { students = await (await Auth.apiFetch('/api/leads?is_student=true', { headers: authHeaders })).json(); }
    catch(e){ students = []; }
}
async function loadHomeworks(){
    try { allHw = await (await Auth.apiFetch('/api/homeworks?teacher_id=' + teacherId, { headers: authHeaders })).json(); }
    catch(e){ allHw = []; }
    renderHomeworks();
}

function createMsg(text, type){
    const el = $('create-msg'); el.innerHTML = text; el.className = `message ${type}`; el.classList.remove('hidden');
}
async function onCreate(e){
    e.preventDefault();
    $('create-msg').classList.add('hidden');
    if (!createStudentId){ createMsg('Выберите ученика', 'error'); return; }
    const description = $('hw-desc').value.trim();
    if (!description){ createMsg('Введите текст задания', 'error'); return; }
    try {
        const r = await Auth.apiFetch('/api/homeworks', {
            method:'POST', headers:{ 'Content-Type':'application/json', ...authHeaders },
            body: JSON.stringify({ teacher_id: teacherId, student_id: createStudentId, description }),
        });
        const data = await r.json();
        if (r.ok){
            createMsg('Задание создано', 'success');
            $('hw-form').reset(); createStudentId = null; $('hw-student-clear').classList.add('hidden');
            await loadHomeworks();
        } else {
            const t = Array.isArray(data.detail) ? data.detail.map(x=>x.msg).join('; ') : (data.detail||'Ошибка');
            createMsg('Ошибка: ' + esc(t), 'error');
        }
    } catch(err){ createMsg('Сетевая ошибка: ' + esc(err.message), 'error'); }
}

function filteredHw(){
    const q = $('f-search').value.trim().toLowerCase();
    const st = $('f-status').value;
    return allHw.filter(h => {
        if (st === 'done' && !h.is_completed) return false;
        if (st === 'open' && h.is_completed) return false;
        if (q && !`${h.student_name||''} ${h.description||''}`.toLowerCase().includes(q)) return false;
        return true;
    });
}

function cardHtml(h){
    const badge = h.is_completed ? '<span class="badge done">✓ Выполнено</span>' : '<span class="badge open">⏳ В работе</span>';
    const toggle = h.is_completed
        ? `<button class="btn-ghost" data-act="toggle" data-id="${h.id}" data-done="1">Вернуть в работу</button>`
        : `<button class="btn-primary" data-act="toggle" data-id="${h.id}" data-done="0">Отметить выполненным</button>`;
    const del = confirming.has(h.id)
        ? `<span class="confirm-row">
               <button class="btn-confirm" data-act="confirm" data-id="${h.id}">Удалить</button>
               <button class="btn-cancel" data-act="cancel" data-id="${h.id}">Отмена</button>
           </span>`
        : `<button class="btn-del" data-act="ask" data-id="${h.id}">Удалить</button>`;
    return `<div class="hw-card" data-id="${h.id}">
        <div class="hw-top"><span class="hw-student">${esc(h.student_name || ('Ученик #'+h.student_id))}</span>${badge}</div>
        <div class="hw-desc">${esc(h.description)}</div>
        <label class="hw-clabel">Вывод по выполнению</label>
        <textarea class="hw-comment" rows="2" placeholder="Комментарий преподавателя...">${esc(h.comment || '')}</textarea>
        <div class="hw-actions">
            <button class="btn-ghost" data-act="save-comment" data-id="${h.id}">Сохранить вывод</button>
            ${toggle}${del}
        </div>
        <div class="hw-foot">создано ${fmtDate(h.created_at)}</div>
    </div>`;
}
function renderHomeworks(){
    const list = filteredHw();
    $('hw-count').textContent = `(${list.length})`;
    $('hw-empty').classList.toggle('hidden', list.length > 0);
    $('hw-list').innerHTML = list.map(cardHtml).join('');
}

$('hw-list').addEventListener('click', async (e) => {
    const btn = e.target.closest('button[data-act]'); if (!btn) return;
    const id = parseInt(btn.dataset.id, 10);
    const act = btn.dataset.act;
    if (act === 'ask'){ confirming.add(id); renderHomeworks(); return; }
    if (act === 'cancel'){ confirming.delete(id); renderHomeworks(); return; }
    if (act === 'confirm'){ await req('/api/homeworks/'+id, { method:'DELETE' }); confirming.delete(id); await loadHomeworks(); return; }
    if (act === 'toggle'){
        const done = btn.dataset.done === '1';
        await req('/api/homeworks/'+id, { method:'PATCH', body: JSON.stringify({ is_completed: !done }) });
        await loadHomeworks(); return;
    }
    if (act === 'save-comment'){
        const comment = btn.closest('.hw-card').querySelector('.hw-comment').value;
        await req('/api/homeworks/'+id, { method:'PATCH', body: JSON.stringify({ comment }) });
        await loadHomeworks(); return;
    }
});
async function req(url, opts){
    try { await Auth.apiFetch(url, { headers:{ 'Content-Type':'application/json', ...authHeaders }, ...opts }); } catch(e){}
}

init();
