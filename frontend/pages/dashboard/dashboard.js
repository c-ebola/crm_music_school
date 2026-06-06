const $ = id => document.getElementById(id);
function esc(s){ const d=document.createElement('div'); d.textContent=s==null?'':String(s); return d.innerHTML; }
function money(v){
  v = Number(v) || 0;
  if (v >= 1000000) return (v/1000000).toFixed(1).replace('.', ',') + ' млн ₽';
  return Math.round(v).toLocaleString('ru-RU') + ' ₽';
}
function short(v){
  if (v >= 1000000) return (v/1000000).toFixed(1) + 'м';
  if (v >= 1000) return Math.round(v/1000) + 'к';
  return String(Math.round(v));
}
function plural(n){
  const a = n % 10, b = n % 100;
  if (a === 1 && b !== 11) return 'е';
  if (a >= 2 && a <= 4 && (b < 10 || b >= 20)) return 'а';
  return 'ов';
}
function deltaText(cur, prev){
  if (prev > 0){
    const pct = Math.round((cur - prev) / prev * 100);
    return (pct >= 0 ? '↑ ' : '↓ ') + Math.abs(pct) + '% к прошлому месяцу';
  }
  if (cur > 0) return 'первые поступления';
  return '—';
}

async function boot(){
  if (!(await Auth.requireRole(['admin','branch_admin']))) return;
  let d;
  try { d = await (await Auth.apiFetch('/api/stats/dashboard')).json(); }
  catch(e){ $('dash').innerHTML = '<div class="empty">Не удалось загрузить статистику</div>'; return; }
  render(d);
}

function render(d){
  $('period').textContent = 'Дашборд сети · ' + d.period;
  $('subtitle').textContent = 'Сводные показатели по ' + d.branches_count + ' филиал' + plural(d.branches_count);

  const k = d.kpi;
  $('kpi').innerHTML = `
    <div class="kpi-card">
      <div class="kpi-label">Выручка сети (месяц)</div>
      <div class="kpi-value">${money(k.revenue)}</div>
      <div class="kpi-delta">${deltaText(k.revenue, k.revenue_prev)}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Активные ученики</div>
      <div class="kpi-value">${k.active_students}</div>
      <div class="kpi-delta">${k.new_students_month > 0 ? '↑ ' + k.new_students_month + ' за месяц' : 'без новых за месяц'}</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">В зоне риска</div>
      <div class="kpi-value risk">${k.at_risk} чел.</div>
      <div class="kpi-delta">без действующего абонемента</div>
    </div>`;

  $('branches-body').innerHTML = d.branches.length
    ? d.branches.map(b => `
      <tr>
        <td><div class="b-name">${esc(b.name)}</div><div class="b-sub">${esc(b.city || '')} · ${b.teachers} преп.</div></td>
        <td>${b.students}</td>
        <td>${money(b.revenue)}</td>
        <td class="${b.debt > 0 ? 'debt' : ''}">${money(b.debt)}</td>
      </tr>`).join('')
    : '<tr><td colspan="4" class="empty">Нет данных по филиалам</td></tr>';

  const rev = d.revenue_by_month;
  const maxRev = Math.max(1, ...rev.map(r => r.amount));
  $('revenue-chart').innerHTML = rev.map((r, i) => {
    const h = Math.round(r.amount / maxRev * 100);
    const last = i === rev.length - 1;
    return `<div class="bar-col">
      <div class="bar-val">${r.amount ? short(r.amount) : ''}</div>
      <div class="bar ${last ? 'bar-cur' : ''}" style="height:${Math.max(h, 2)}%;"></div>
      <div class="bar-lbl">${esc(r.month)}</div>
    </div>`;
  }).join('');

  const tmax = Math.max(1, ...d.top_teachers.map(t => t.sessions));
  $('top-teachers').innerHTML = d.top_teachers.length
    ? d.top_teachers.map((t, i) => `
      <div class="hb-row">
        <div class="hb-name">${esc(t.name)}<span class="hb-sub">${esc(t.branch || '')}</span></div>
        <div class="hb-track"><div class="hb-fill c${i % 3}" style="width:${Math.round(t.sessions / tmax * 100)}%;"></div></div>
        <div class="hb-val">${t.sessions} зан.</div>
      </div>`).join('')
    : '<div class="empty">Занятий пока нет</div>';

  const dmax = Math.max(1, ...d.disciplines.map(x => x.students));
  $('disciplines').innerHTML = d.disciplines.length
    ? d.disciplines.map(x => `
      <div class="hb-row">
        <div class="hb-name">${esc(x.name)}</div>
        <div class="hb-track"><div class="hb-fill" style="width:${Math.round(x.students / dmax * 100)}%;"></div></div>
        <div class="hb-val">${x.students} уч.</div>
      </div>`).join('')
    : '<div class="empty">Нет учеников</div>';
}

boot();
