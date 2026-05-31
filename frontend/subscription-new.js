const studentSel = document.getElementById('f_student');
const planSel = document.getElementById('f_plan');
const startInput = document.getElementById('f_start');
const preview = document.getElementById('plan-preview');
const message = document.getElementById('message');
const result = document.getElementById('result');
const form = document.getElementById('sub-form');

let plansCache = [];

function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function money(v){ return Number(v).toLocaleString('ru-RU') + ' ₽'; }
function fmtDate(iso){ if(!iso) return ''; return new Date(iso).toLocaleDateString('ru-RU'); }

async function loadStudents() {
    try {
        const r = await fetch('/api/leads?is_student=true');
        const students = await r.json();
        if (!students.length) {
            studentSel.innerHTML = '<option value="">Нет учеников — сначала сконвертируйте лид</option>';
            return;
        }
        studentSel.innerHTML = '<option value="">— выберите ученика —</option>' +
            students.map(s => {
                const name = s.student_full_name || s.contact_full_name;
                return `<option value="${s.id}">${esc(name)} (№${s.id})</option>`;
            }).join('');
    } catch(e) { studentSel.innerHTML = '<option value="">Ошибка загрузки учеников</option>'; }
}

async function loadPlans() {
    try {
        const r = await fetch('/api/subscription-plans?only_active=true');
        plansCache = await r.json();
        if (!plansCache.length) {
            planSel.innerHTML = '<option value="">Нет активных тарифов — создайте в каталоге</option>';
            return;
        }
        planSel.innerHTML = '<option value="">— выберите тариф —</option>' +
            plansCache.map(p => `<option value="${p.id}">${esc(p.name)} — ${money(p.price)}</option>`).join('');
    } catch(e) { planSel.innerHTML = '<option value="">Ошибка загрузки тарифов</option>'; }
}

planSel.addEventListener('change', () => {
    const plan = plansCache.find(p => String(p.id) === planSel.value);
    if (!plan) { preview.classList.remove('show'); return; }
    preview.innerHTML = `
        <div class="row"><span>Тариф</span><span>${esc(plan.name)}</span></div>
        <div class="row"><span>Занятий</span><span>${plan.lessons_count}</span></div>
        <div class="row"><span>Срок действия</span><span>${plan.duration_days} дней</span></div>
        <div class="row"><span>Стоимость</span><span class="price">${money(plan.price)}</span></div>
        ${plan.description ? `<div class="row"><span>Описание</span><span>${esc(plan.description)}</span></div>` : ''}
    `;
    preview.classList.add('show');
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    message.classList.add('hidden');
    result.classList.remove('show');

    const payload = {
        student_id: parseInt(studentSel.value, 10),
        plan_id: parseInt(planSel.value, 10),
    };
    if (startInput.value) payload.start_date = startInput.value;

    try {
        const r = await fetch('/api/subscriptions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await r.json();
        if (r.ok) {
            result.innerHTML = `
                <div style="margin-bottom:8px;"><span class="big">Абонемент оформлен</span></div>
                <div class="row"><span>Ученик</span><span>${esc(data.student_name)}</span></div>
                <div class="row"><span>Тариф</span><span>${esc(data.plan_name)}</span></div>
                <div class="row"><span>Занятий доступно</span><span>${data.lessons_remaining} из ${data.lessons_total}</span></div>
                <div class="row"><span>Оплачено</span><span>${money(data.price_paid)}</span></div>
                <div class="row"><span>Период</span><span>${fmtDate(data.start_date)} — ${fmtDate(data.end_date)}</span></div>
            `;
            result.classList.add('show');
            form.reset();
            preview.classList.remove('show');
        } else {
            const detail = Array.isArray(data.detail) ? data.detail.map(x=>x.msg).join('; ') : (data.detail||'Ошибка');
            message.textContent = 'Ошибка: ' + detail;
            message.className = 'message error';
        }
    } catch(e) {
        message.textContent = 'Сетевая ошибка: ' + e.message;
        message.className = 'message error';
    }
});

loadStudents();
loadPlans();
