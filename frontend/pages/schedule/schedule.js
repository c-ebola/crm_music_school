const QUANTS = 10;
const dayInput = document.getElementById('day');
const gridBody = document.getElementById('grid-body');
const overlay = document.getElementById('overlay');
const lessonSel = document.getElementById('m_lesson');
const roomSel = document.getElementById('m_room');
const modalMessage = document.getElementById('modal-message');

let lessonsCache = [];
let currentQuant = null;

function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':s; return d.innerHTML; }
function pad(n){ return String(n).padStart(2,'0'); }
function teacherName(t){ return t ? [t.last_name, t.first_name].filter(Boolean).join(' ') : ''; }

function quantTime(q) {
    const startMin = (q - 1) * 60;       // от 9:00
    const sTotal = 9 * 60 + startMin;
    const eTotal = sTotal + 45;          // урок 45 мин
    return `${pad(Math.floor(sTotal/60))}:${pad(sTotal%60)}–${pad(Math.floor(eTotal/60))}:${pad(eTotal%60)}`;
}

async function loadDicts() {
    try {
        const [lr, rr] = await Promise.all([
            fetch('/api/lessons'),
            fetch('/api/rooms?only_active=true'),
        ]);
        lessonsCache = await lr.json();
        const rooms = await rr.json();
        lessonSel.innerHTML = lessonsCache.map(l => {
            const disc = l.discipline ? l.discipline.name : '—';
            const t = teacherName(l.teacher);
            return `<option value="${l.id}">${esc(disc)}${t ? ' — ' + esc(t) : ''}${l.lesson_type ? ' ('+esc(l.lesson_type)+')' : ''}</option>`;
        }).join('') || '<option value="">Нет занятий — создайте в /api/lessons</option>';
        roomSel.innerHTML = '<option value="">— без кабинета —</option>' +
            rooms.map(r => `<option value="${r.id}">${esc(r.name)}</option>`).join('');
    } catch(e) { /* оставим пустыми */ }
}

async function loadGrid() {
    const day = dayInput.value;
    let entries = [];
    try {
        const r = await fetch('/api/schedule?day=' + day);
        entries = await r.json();
    } catch(e) { /* пусто */ }

    // группируем по кванту
    const byQuant = {};
    entries.forEach(e => { (byQuant[e.quant] = byQuant[e.quant] || []).push(e); });

    let html = '';
    for (let q = 1; q <= QUANTS; q++) {
        const items = (byQuant[q] || []).map(e => {
            const s = e.session;
            const disc = s && s.lesson && s.lesson.discipline ? s.lesson.discipline.name : '—';
            const t = s && s.lesson ? teacherName(s.lesson.teacher) : '';
            const room = s && s.room ? s.room.name : 'без кабинета';
            return `<div class="sess">
                <button class="del" data-id="${e.id}" title="Убрать">&times;</button>
                <div class="disc">${esc(disc)}</div>
                <div class="meta">${esc(t)} · ${esc(room)}</div>
            </div>`;
        }).join('');
        html += `<tr>
            <td class="qtime">Урок ${q}<br>${quantTime(q)}</td>
            <td class="slot">${items || '<span style="color:#aaa;">—</span>'}</td>
            <td><button class="add-btn" data-quant="${q}">+ Добавить</button></td>
        </tr>`;
    }
    gridBody.innerHTML = html;

    document.querySelectorAll('.add-btn').forEach(b =>
        b.addEventListener('click', () => openModal(parseInt(b.dataset.quant, 10))));
    document.querySelectorAll('.sess .del').forEach(b =>
        b.addEventListener('click', () => removeEntry(b.dataset.id)));
}

function openModal(quant) {
    currentQuant = quant;
    modalMessage.classList.add('hidden');
    document.getElementById('modal-title').textContent = `Добавить занятие — урок ${quant} (${quantTime(quant)})`;
    overlay.classList.add('show');
}
function closeModal() { overlay.classList.remove('show'); currentQuant = null; }

document.getElementById('m_cancel').addEventListener('click', closeModal);
overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });

document.getElementById('m_save').addEventListener('click', async () => {
    modalMessage.classList.add('hidden');
    if (!lessonSel.value) {
        modalMessage.textContent = 'Выберите занятие';
        modalMessage.className = 'message error';
        return;
    }
    const payload = {
        day: dayInput.value,
        quant: currentQuant,
        lesson_id: parseInt(lessonSel.value, 10),
        room_id: roomSel.value ? parseInt(roomSel.value, 10) : null,
    };
    try {
        const r = await fetch('/api/schedule/add-session', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        if (r.ok) { closeModal(); loadGrid(); }
        else {
            const err = await r.json();
            modalMessage.textContent = 'Ошибка: ' + (err.detail || r.status);
            modalMessage.className = 'message error';
        }
    } catch(e) {
        modalMessage.textContent = 'Сетевая ошибка: ' + e.message;
        modalMessage.className = 'message error';
    }
});

async function removeEntry(id) {
    try {
        await fetch('/api/schedule/' + id, { method: 'DELETE' });
        loadGrid();
    } catch(e) { alert('Ошибка: ' + e.message); }
}

dayInput.addEventListener('change', loadGrid);

// старт: сегодня
dayInput.value = new Date().toISOString().slice(0, 10);
loadDicts();
loadGrid();
