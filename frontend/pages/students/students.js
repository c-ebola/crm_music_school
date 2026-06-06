const $ = id => document.getElementById(id);
function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':String(s); return d.innerHTML; }

const SS_LABEL = { active:'Активен', paused:'На паузе', finished:'Завершил', dropped:'Ушёл' };

let students = [], disciplines = [], branches = [], teachers = [];
let selectedId = null;
let canIssue = false;

async function boot(){
  if (!(await Auth.requireRole(['manager','branch_admin','admin']))) return;
  const me = await Auth.getMe();
  canIssue = !!(me && (me.is_superuser || (me.role && ['branch_admin','admin'].includes(me.role.code))));
  await Promise.all([loadRefs(), loadStudents()]);
}

async function loadRefs(){
  try { disciplines = await (await Auth.apiFetch('/api/disciplines?only_active=true')).json(); } catch(e){ disciplines=[]; }
  try { branches = await (await Auth.apiFetch('/api/branches?kind=school&only_active=true')).json(); } catch(e){ branches=[]; }
  try { teachers = await (await Auth.apiFetch('/api/users/teachers')).json(); } catch(e){ teachers=[]; }
  $('e_discipline').innerHTML = (disciplines||[]).map(d=>`<option value="${d.id}">${esc(d.name)}</option>`).join('');
  $('e_branch').innerHTML = '<option value="">— не выбран —</option>' +
    (branches||[]).map(b=>`<option value="${b.id}">${esc(b.name)}</option>`).join('');
  $('e_teacher').innerHTML = '<option value="">— не назначен —</option>' +
    (teachers||[]).map(t=>{ const fio=[t.last_name,t.first_name].filter(Boolean).join(' '); return `<option value="${t.id}">${esc(fio)}</option>`; }).join('');
}

async function loadStudents(){
  try { const r = await Auth.apiFetch('/api/leads?is_student=true'); const d = await r.json(); students = Array.isArray(d)?d:[]; }
  catch(e){ students = []; }
  renderList();
}

function studentName(s){ return s.student_full_name || s.contact_full_name || ('Ученик №'+s.id); }

function renderList(){
  const q = $('st-search').value.trim().toLowerCase();
  const list = students.filter(s => !q || studentName(s).toLowerCase().includes(q));
  $('st-empty').classList.toggle('hidden', list.length > 0);
  $('st-list').innerHTML = list.map(s => {
    const st = s.student_status || 'active';
    return `<div class="st-item ${String(s.id)===String(selectedId)?'active':''}" data-id="${s.id}">
      <div class="st-name">${esc(studentName(s))}</div>
      <div class="st-sub">${esc(s.discipline ? s.discipline.name : '—')} · <span class="badge b-${st}">${esc(SS_LABEL[st]||st)}</span></div>
    </div>`;
  }).join('');
}

$('st-search').addEventListener('input', renderList);

$('st-list').addEventListener('click', (e) => {
  const item = e.target.closest('.st-item');
  if (!item) return;
  selectedId = item.dataset.id;
  renderList();
  openEdit(students.find(s => String(s.id) === selectedId));
});

function openEdit(s){
  if (!s) return;
  $('edit-title').textContent = studentName(s);
  $('e_student_name').value = s.student_full_name || '';
  $('e_contact_name').value = s.contact_full_name || '';
  $('e_contact_type').value = s.contact_type || 'parent';
  $('e_status').value = s.student_status || 'active';
  $('e_email').value = s.email || '';
  $('e_phone').value = s.phone || '';
  $('e_telegram').value = s.telegram || '';
  $('e_age').value = s.student_age != null ? s.student_age : '';
  $('e_discipline').value = s.discipline_id || '';
  $('e_level').value = s.level || '';
  $('e_format').value = s.lesson_format || '';
  $('e_branch').value = s.branch_id || '';
  $('e_teacher').value = s.teacher_id || '';
  $('e_comment').value = s.manager_comment || '';
  $('edit-msg').classList.add('hidden');
  $('edit-card').style.display = '';
  renderCred(s);
}

function msg(text, type){ const el=$('edit-msg'); el.textContent=text; el.className=`message ${type}`; el.classList.remove('hidden'); }

$('edit-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!selectedId) return;
  const num = v => v ? parseInt(v, 10) : null;
  const payload = {
    student_full_name: $('e_student_name').value.trim() || null,
    contact_full_name: $('e_contact_name').value.trim(),
    contact_type: $('e_contact_type').value,
    student_status: $('e_status').value,
    email: $('e_email').value.trim(),
    phone: $('e_phone').value.trim() || null,
    telegram: $('e_telegram').value.trim() || null,
    student_age: $('e_age').value ? parseInt($('e_age').value, 10) : null,
    discipline_id: num($('e_discipline').value),
    level: $('e_level').value || null,
    lesson_format: $('e_format').value || null,
    branch_id: num($('e_branch').value),
    teacher_id: num($('e_teacher').value),
    manager_comment: $('e_comment').value.trim() || null,
  };
  try {
    const r = await Auth.apiFetch('/api/leads/' + selectedId, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
    });
    const data = await r.json();
    if (r.ok) {
      msg('Сохранено', 'success');
      const i = students.findIndex(s => String(s.id) === String(selectedId));
      if (i >= 0) students[i] = data;
      renderList();
      $('edit-title').textContent = studentName(data);
    } else {
      const detail = Array.isArray(data.detail) ? data.detail.map(x=>x.msg).join('; ') : (data.detail || 'Ошибка');
      msg('Ошибка: ' + detail, 'error');
    }
  } catch(err){ msg('Сетевая ошибка: ' + err.message, 'error'); }
});

// ===== Доступ в систему =====
function renderCred(s){
  const box = $('cred-box');
  if (!canIssue){ box.innerHTML = ''; return; }
  if (s.user_id){
    box.innerHTML = `<div class="cred-title">Доступ в систему</div>
      <div class="cred-row"><span style="color:#1d6e1d;">✓ Аккаунт ученика создан</span>
        <button type="button" class="btn-ghost" id="cred-reset">Сбросить пароль</button></div>
      <div id="cred-out" class="cred-out hidden"></div>`;
    $('cred-reset').addEventListener('click', () => resetCred(s.id));
  } else {
    box.innerHTML = `<div class="cred-title">Доступ в систему</div>
      <div class="cred-row">
        <input type="email" id="cred-email" placeholder="email для входа" value="${esc(s.email||'')}" style="flex:1;">
        <button type="button" class="btn-ghost" id="cred-issue">Выдать доступ</button>
      </div>
      <div id="cred-out" class="cred-out hidden"></div>`;
    $('cred-issue').addEventListener('click', () => issueCred(s.id));
  }
}

function showCredOut(data){
  const out = $('cred-out');
  out.innerHTML = `<div class="cred-warn">Сохраните данные — пароль показывается один раз:</div>
    <div class="cred-creds">Логин: <code>${esc(data.email)}</code><br>Пароль: <code>${esc(data.password)}</code></div>`;
  out.classList.remove('hidden');
}
function showCredErr(detail){
  const out = $('cred-out');
  out.innerHTML = `<div class="cred-err">${esc(typeof detail === 'string' ? detail : 'Ошибка')}</div>`;
  out.classList.remove('hidden');
}

async function issueCred(id){
  const email = ($('cred-email') ? $('cred-email').value : '').trim();
  try {
    const r = await Auth.apiFetch('/api/leads/' + id + '/credentials', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ email: email || null }),
    });
    const data = await r.json();
    if (r.ok){
      const i = students.findIndex(s => String(s.id) === String(id));
      if (i >= 0) students[i].user_id = data.user_id;
      renderCred(students[i]);
      showCredOut(data);
    } else { showCredErr(data.detail); }
  } catch(e){ showCredErr('Сетевая ошибка: ' + e.message); }
}

async function resetCred(id){
  try {
    const r = await Auth.apiFetch('/api/leads/' + id + '/credentials/reset', { method:'POST' });
    const data = await r.json();
    if (r.ok){ showCredOut(data); } else { showCredErr(data.detail); }
  } catch(e){ showCredErr('Сетевая ошибка: ' + e.message); }
}

boot();
