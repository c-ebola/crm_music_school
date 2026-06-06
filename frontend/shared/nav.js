// Единое боковое меню по роли. Требует подключённый ранее auth.js.
// На странице должен быть контейнер сайдбара: <aside id="sidebar"></aside>

(function () {
  const ROLE_NAMES = {
    admin: 'Админ сети',
    branch_admin: 'Админ филиала',
    methodist: 'Методист',
    accountant: 'Бухгалтер',
    manager: 'Менеджер',
    teacher: 'Преподаватель',
  };

  const HOME = { label: 'Главный экран', href: '/' };
  const DASHBOARD = { label: 'Панель управления', href: '/dashboard' };
  const LEADS = { label: 'Новый лид', href: '/leads' };
  const CONVERT = { label: 'Конверсия в ученика', href: '/convert' };
  const PLANS = { label: 'Каталог абонементов', href: '/plans' };
  const SUB_NEW = { label: 'Оформить абонемент', href: '/subscription-new' };
  const PAY_NEW = { label: 'Фиксация оплаты', href: '/payment-new' };
  const STUDENT_FIN = { label: 'Финансы ученика', href: '/student-finance' };
  const CONFIRM_PAY = { label: 'Подтверждение оплат', href: '/confirm-payments' };
  const SCHEDULE = { label: 'Расписание', href: '/schedule' };
  const LESSONS = { label: 'Уроки', href: '/lessons' };
  const STUDENT_SCHED = { label: 'Расписание ученика', href: '/student-schedule' };
  const MY_SCHED = { label: 'Моё расписание', href: '/my-schedule' };
  const HOMEWORKS = { label: 'Домашние задания', href: '/homeworks' };
  const USERS = { label: 'Пользователи', href: '/users' };
  const CONCERTS = { label: 'Концерты', href: '/events' };
  const EXAMS = { label: 'Экзамены', href: '/exams' };
  const COMMISSIONS = { label: 'Комиссии', href: '/commissions' };
  const BRANCHES = { label: 'Филиалы', href: '/branches' };
  const FUNNEL = { label: 'Воронка', href: '/funnel' };

  // Набор пунктов роли = страницы, которые роль может открыть

const NAV = {
    manager: [HOME, LEADS, FUNNEL, CONVERT],
    accountant: [HOME, PLANS, SUB_NEW, PAY_NEW, STUDENT_FIN],
    methodist: [HOME, SCHEDULE, LESSONS, STUDENT_SCHED, CONCERTS, EXAMS, COMMISSIONS],
    teacher: [HOME, MY_SCHED, HOMEWORKS],
    branch_admin: [HOME, DASHBOARD, LEADS, FUNNEL, CONVERT,
      SCHEDULE, STUDENT_SCHED, LESSONS, CONFIRM_PAY, CONCERTS, EXAMS, COMMISSIONS],
    admin: [HOME, DASHBOARD, LEADS, FUNNEL, CONVERT,
      PLANS, SUB_NEW, PAY_NEW, STUDENT_FIN, CONFIRM_PAY,
      SCHEDULE, LESSONS, STUDENT_SCHED, USERS, BRANCHES, CONCERTS, EXAMS, COMMISSIONS],
  };

  function esc(s) { const d = document.createElement('div'); d.textContent = s == null ? '' : s; return d.innerHTML; }
  function norm(p) { return (p || '').replace(/\/+$/, '') || '/'; }

  function render(me) {
    const role = me && me.role ? me.role.code : null;
    const items = NAV[role] || (me && me.is_superuser ? NAV.admin : [HOME]);
    const path = norm(window.location.pathname);
    const links = items.map(function (it) {
      const active = norm(it.href) === path ? ' active' : '';
      return '<a href="' + it.href + '" class="nav-item' + active + '">' + esc(it.label) + '</a>';
    }).join('');
    const name = me ? (me.full_name || me.email || '') : '';
    const roleName = ROLE_NAMES[role] || (me && me.is_superuser ? 'Админ сети' : '—');
    return '' +
      '<div class="brand">♪ МузCRM</div>' +
      '<div class="brand-sub">' + esc(roleName) + '</div>' +
      '<nav class="nav">' + links + '</nav>' +
      '<div style="margin-top:24px; padding-top:16px; border-top:1px solid #e5e5ea;">' +
        '<div style="font-size:13px; color:#86868b; margin-bottom:8px;">' + esc(name) + '</div>' +
        '<button id="nav-logout" style="width:100%; padding:8px; border:1px solid #d2d2d7; border-radius:8px; background:#fff; cursor:pointer; font-size:13px;">Выход</button>' +
      '</div>';
  }

  // Находим сайдбар максимально широко: по id, по классу, либо первый <aside>

  function findSidebar() {
    return document.getElementById('sidebar')
        || document.querySelector('aside.sidebar')
        || document.querySelector('.layout > aside')
        || document.querySelector('aside');
  }

  async function mount() {
    const aside = findSidebar();
    if (!aside) return;
    aside.id = 'sidebar';
    aside.classList.add('sidebar');
    let me = null;
    try { me = await window.Auth.getMe(); } catch (e) { return; }
    aside.innerHTML = render(me);   // ← затираем любые зашитые ссылки
    const lo = document.getElementById('nav-logout');
    if (lo) lo.addEventListener('click', function () { window.Auth.logout(); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();