const subSel = document.getElementById('f_sub');
const preview = document.getElementById('sub-preview');
const amountInput = document.getElementById('f_amount');
const dateInput = document.getElementById('f_date');
const message = document.getElementById('message');
const result = document.getElementById('result');
const form = document.getElementById('pay-form');

const METHODS = { cash: "Наличные", card: "Карта", transfer: "Перевод" };
const STATUSES = { pending: "Ожидает подтверждения", confirmed: "Подтверждён", rejected: "Отклонён" };

let subsCache = [];

function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function money(v){ return Number(v).toLocaleString('ru-RU') + ' ₽'; }
function fmtDate(iso){ if(!iso) return ''; return new Date(iso).toLocaleDateString('ru-RU'); }

async function loadSubscriptions() {
    try {
        const r = await fetch('/api/subscriptions');
        subsCache = await r.json();
        if (!subsCache.length) {
            subSel.innerHTML = '<option value="">Нет абонементов — сначала оформите</option>';
            return;
        }
        subSel.innerHTML = '<option value="">— выберите абонемент —</option>' +
            subsCache.map(s =>
                `<option value="${s.id}">№${s.id} · ${esc(s.student_name||'')} · ${esc(s.plan_name||'')} (${money(s.price_paid)})</option>`
            ).join('');
    } catch(e) { subSel.innerHTML = '<option value="">Ошибка загрузки абонементов</option>'; }
}

subSel.addEventListener('change', () => {
    const sub = subsCache.find(s => String(s.id) === subSel.value);
    if (!sub) { preview.classList.remove('show'); return; }
    preview.innerHTML = `
        <div class="row"><span>Ученик</span><span>${esc(sub.student_name||'—')}</span></div>
        <div class="row"><span>Тариф</span><span>${esc(sub.plan_name||'—')}</span></div>
        <div class="row"><span>Стоимость абонемента</span><span>${money(sub.price_paid)}</span></div>
        <div class="row"><span>Занятий</span><span>${sub.lessons_remaining} из ${sub.lessons_total}</span></div>
        <div class="row"><span>Период</span><span>${fmtDate(sub.start_date)} — ${fmtDate(sub.end_date)}</span></div>
    `;
    preview.classList.add('show');
    // подставляем сумму из абонемента (можно изменить)
    amountInput.value = sub.price_paid;
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    message.classList.add('hidden');
    result.classList.remove('show');

    const payload = {
        subscription_id: parseInt(subSel.value, 10),
        amount: parseFloat(amountInput.value),
        method: document.getElementById('f_method').value,
        comment: document.getElementById('f_comment').value.trim() || null,
    };
    if (dateInput.value) payload.payment_date = dateInput.value;

    try {
        const r = await fetch('/api/payments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await r.json();
        if (r.ok) {
            result.innerHTML = `
                <div style="margin-bottom:8px;"><span class="big">Оплата зафиксирована</span></div>
                <div class="row"><span>Ученик</span><span>${esc(data.student_name||'—')}</span></div>
                <div class="row"><span>Тариф</span><span>${esc(data.plan_name||'—')}</span></div>
                <div class="row"><span>Сумма</span><span>${money(data.amount)}</span></div>
                <div class="row"><span>Способ</span><span>${esc(METHODS[data.method]||data.method)}</span></div>
                <div class="row"><span>Дата</span><span>${fmtDate(data.payment_date)}</span></div>
                <div class="row"><span>Статус</span><span class="badge">${esc(STATUSES[data.status]||data.status)}</span></div>
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

loadSubscriptions();
