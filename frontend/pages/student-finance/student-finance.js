Auth.requireRole(['accountant', 'admin']);

const studentSel = document.getElementById('f_student');
const content = document.getElementById('content');
const summary = document.getElementById('summary');
const subsTbody = document.getElementById('subs-tbody');
const paysTbody = document.getElementById('pays-tbody');

const SUB_STATUS = { active:"Действует", expired:"Истёк", used_up:"Занятия закончились", cancelled:"Отменён" };
const PAY_STATUS = { pending:"Ожидает", confirmed:"Подтверждён", rejected:"Отклонён" };
const METHODS = { cash:"Наличные", card:"Карта", transfer:"Перевод" };

function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function money(v){ return Number(v).toLocaleString('ru-RU') + ' ₽'; }
function fmtDate(iso){ if(!iso) return ''; return new Date(iso).toLocaleDateString('ru-RU'); }

async function loadStudents() {
    try {
        const r = await Auth.apiFetch('/api/leads?is_student=true');
        const students = await r.json();
        if (!students.length) {
            studentSel.innerHTML = '<option value="">Нет учеников</option>';
            return;
        }
        studentSel.innerHTML = '<option value="">— выберите ученика —</option>' +
            students.map(s => {
                const name = s.student_full_name || s.contact_full_name;
                return `<option value="${s.id}">${esc(name)} (№${s.id})</option>`;
            }).join('');
    } catch(e) { studentSel.innerHTML = '<option value="">Ошибка загрузки</option>'; }
}

async function loadFinance(studentId) {
    try {
        const [subsR, paysR] = await Promise.all([
            Auth.apiFetch('/api/subscriptions?student_id=' + studentId),
            Auth.apiFetch('/api/payments?student_id=' + studentId),
        ]);
        const subs = await subsR.json();
        const pays = await paysR.json();

        // Абонементы
        subsTbody.innerHTML = subs.length ? subs.map(s => `
            <tr>
                <td>${s.id}</td>
                <td>${esc(s.plan_name||'—')}</td>
                <td>${s.lessons_remaining} из ${s.lessons_total}</td>
                <td>${money(s.price_paid)}</td>
                <td>${fmtDate(s.start_date)} — ${fmtDate(s.end_date)}</td>
                <td><span class="badge b-${s.status}">${esc(SUB_STATUS[s.status]||s.status)}</span></td>
            </tr>`).join('') : '<tr><td colspan="6" class="empty">Абонементов нет</td></tr>';

        // Оплаты
        paysTbody.innerHTML = pays.length ? pays.map(p => `
            <tr>
                <td>${p.id}</td>
                <td>${fmtDate(p.payment_date)}</td>
                <td>${money(p.amount)}</td>
                <td>${esc(METHODS[p.method]||p.method)}</td>
                <td>${esc(p.plan_name||'—')}</td>
                <td><span class="badge b-${p.status}">${esc(PAY_STATUS[p.status]||p.status)}</span></td>
            </tr>`).join('') : '<tr><td colspan="6" class="empty">Оплат нет</td></tr>';

        // Сводка
        const confirmed = pays.filter(p => p.status === 'confirmed').reduce((a,p)=>a+Number(p.amount),0);
        const pending = pays.filter(p => p.status === 'pending').reduce((a,p)=>a+Number(p.amount),0);
        summary.innerHTML = `
            <div class="stat"><div class="label">Абонементов</div><div class="value">${subs.length}</div></div>
            <div class="stat green"><div class="label">Оплачено (подтверждено)</div><div class="value">${money(confirmed)}</div></div>
            <div class="stat amber"><div class="label">Ожидает подтверждения</div><div class="value">${money(pending)}</div></div>
        `;

        content.classList.remove('hidden');
    } catch(e) {
        content.classList.remove('hidden');
        summary.innerHTML = `<div class="stat"><div class="label">Ошибка</div><div class="value">${esc(e.message)}</div></div>`;
    }
}

studentSel.addEventListener('change', () => {
    if (studentSel.value) loadFinance(studentSel.value);
    else content.classList.add('hidden');
});

loadStudents();
